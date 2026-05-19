# ============================================================
# Experiment: exp_114
# Agent: Cindy
# Source: exp_114
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    my_current_budget = my_status['budget']
    my_current_hp = my_status['hp']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If I'm the only one left, bid minimal to save budget
    if num_alive_opponents == 0:
        return min(my_current_budget, WATER_REQ * 1.5)

    # Urgency based on my HP (Health Points)
    # If HP is very low, I MUST get water. Bid very aggressively.
    if my_current_hp <= 1:
        return min(my_current_budget, DAILY_SALARY * 0.95)
    if my_current_hp <= 2:
        return min(my_current_budget, DAILY_SALARY * 0.8)
    if my_current_hp <= 3:
        return min(my_current_budget, DAILY_SALARY * 0.65)

    # Analyze opponent's previous bids and states
    highest_prev_bid = 0
    weakest_opponent_id = None
    weakest_opponent_hp = 100 # Initialize with a high value
    weakest_opponent_budget = 100000 # Initialize with a high value

    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                highest_prev_bid = max(highest_prev_bid, prev_trace['bid'])

            # Identify the weakest opponent (lowest HP, then lowest budget)
            if opp_data['hp'] < weakest_opponent_hp:
                weakest_opponent_hp = opp_data['hp']
                weakest_opponent_id = opp_id
                weakest_opponent_budget = opp_data['budget']
            elif opp_data['hp'] == weakest_opponent_hp and opp_data['budget'] < weakest_opponent_budget:
                weakest_opponent_budget = opp_data['budget']
                weakest_opponent_id = opp_id

    # Base bid, if no strong signals from previous bids
    target_bid = DAILY_SALARY * 0.5

    # Adjust bid based on highest previous opponent bid
    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.7: # Opponents are bidding very high
            target_bid = highest_prev_bid + (DAILY_SALARY * 0.05) # Slightly outbid
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Opponents are bidding moderately
            target_bid = highest_prev_bid + (DAILY_SALARY * 0.02) # Slightly outbid
        else: # Opponents are bidding low
            target_bid = max(highest_prev_bid + 1, DAILY_SALARY * 0.4) # Ensure a competitive bid

    # Strategy to eliminate weakest opponent
    # Only if I'm not in critical HP myself and the opponent is very weak
    if weakest_opponent_id and weakest_opponent_hp <= 2 and my_current_hp > 3:
        # Bid high enough to potentially outbid them, considering their budget
        bid_to_eliminate = max(target_bid, weakest_opponent_budget + 1, DAILY_SALARY * 0.8)
        target_bid = min(bid_to_eliminate, DAILY_SALARY * 0.9) # Don't overspend too much

    # Ensure bid is at least enough to cover water cost, or a reasonable minimum
    target_bid = max(target_bid, WATER_REQ * 2) # A bit higher than absolute minimum to be competitive

    # Final bid must not exceed current budget
    final_bid = min(my_current_budget, target_bid)

    # Ensure bid is at least 1.0 to avoid errors or unintended behavior
    return max(1.0, final_bid)
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

    bid = DAILY_SALARY * 0.5 # Base bid

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_prev_bid = 0.0
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)

    # --- Bid Adjustments ---

    # 1. Critical HP / No Water Days: Survival is paramount
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        bid = DAILY_SALARY * 1.1 # Bid very aggressively to secure water
    elif my_status['hp'] <= 5:
        bid = max(bid, DAILY_SALARY * 0.85) # High priority, but not critical yet

    # 2. React to Opponent Aggression (from yesterday's trace)
    if max_prev_bid > 0:
        if max_prev_bid >= DAILY_SALARY * 0.9: # Opponents are very aggressive
            if my_status['hp'] > 5: # If my HP is good, be competitive but not reckless
                bid = max(bid, DAILY_SALARY * 0.7)
            else: # If my HP is low, match or slightly exceed high bids
                bid = max(bid, max_prev_bid + 5)
        elif max_prev_bid >= DAILY_SALARY * 0.5: # Moderate opponent aggression
            bid = max(bid, max_prev_bid + 2) # Slightly exceed to win

    # 3. Adjust for Supply Scarcity
    total_water_needed_estimate = WATER_REQ * (num_alive_opponents + 1)
    
    if day_context['supply'] < total_water_needed_estimate:
        if my_status['hp'] > 5:
            bid = max(bid, DAILY_SALARY * 0.75)
        else:
            bid = max(bid, DAILY_SALARY * 0.95)
    elif day_context['supply'] >= total_water_needed_estimate + WATER_REQ * 2:
        if my_status['hp'] > 5 and my_status['budget'] > DAILY_SALARY * 5:
            bid = min(bid, DAILY_SALARY * 0.4)

    # 4. End-Game Pressure
    days_left = EPISODE_DAYS - day_context['day']
    if days_left <= 2:
        if my_status['hp'] < 10:
            bid = max(bid, DAILY_SALARY * 1.05)
        else:
            bid = max(bid, DAILY_SALARY * 0.6)
    elif days_left <= 4:
        if my_status['hp'] < 7:
            bid = max(bid, DAILY_SALARY * 0.9)

    # Final constraints
    bid = min(bid, my_status['budget'])
    bid = max(0.0, bid)

    if bid < DAILY_SALARY * 0.2 and my_status['hp'] < 10 and my_status['budget'] >= DAILY_SALARY * 0.2:
        bid = DAILY_SALARY * 0.2

    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # Based on Current Meta-Round State

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Scenario 1: No active opponents (I am the only one left)
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1) # Bid low to conserve budget

    # Scenario 2: Critical HP or missed water recently
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        return min(my_status['budget'], DAILY_SALARY * 0.95) # Bid very aggressively to survive

    # Scenario 3: End game approaching, need to secure water
    # Day 1 is 1, Day 10 is 10. For last 2 days (9, 10), condition is day >= 9.
    if day_context['day'] >= EPISODE_DAYS - 1:
        return min(my_status['budget'], DAILY_SALARY * 0.9) # Aggressive bid

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Default bid if no specific conditions trigger
    bid_amount = DAILY_SALARY * 0.55

    # Bidding logic based on number of opponents and their previous bids
    if num_alive_opponents >= 2: # High competition
        if highest_prev_bid > DAILY_SALARY * 0.8: # Opponents are very aggressive
            bid_amount = highest_prev_bid + 2.0
        elif highest_prev_bid > DAILY_SALARY * 0.6: # Opponents are moderately aggressive
            bid_amount = max(DAILY_SALARY * 0.7, highest_prev_bid + 5.0)
        else: # Opponents bidding low or no history, establish dominance
            bid_amount = DAILY_SALARY * 0.75
    else: # num_alive_opponents == 1 (one opponent left)
        if highest_prev_bid > DAILY_SALARY * 0.7: # Single opponent is aggressive
            bid_amount = highest_prev_bid + 1.0
        else: # Single opponent is not very aggressive, or no history
            bid_amount = max(DAILY_SALARY * 0.55, highest_prev_bid + 5.0)

    # Ensure bid does not exceed budget and is positive
    final_bid = min(my_status['budget'], bid_amount)
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    # Initialize Alex's previous bid
    alex_prev_bid = 0.0
    alex_found = False

    # Search for Alex's previous bid
    for opp_id, opp_data in opponents_status.items():
        if opp_id == "Alex":
            alex_found = True
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                alex_prev_bid = prev['bid']
            break

    # Base bid: A strong default bid to win against weaker opponents
    bid = DAILY_SALARY * 0.85

    # Adjust bid based on Alex's previous action if Alex is found and has a valid previous bid
    if alex_found and alex_prev_bid > 0:
        # If Alex bid aggressively (e.g., more than 70% of daily salary)
        if alex_prev_bid >= DAILY_SALARY * 0.7:
            bid = max(bid, alex_prev_bid + 5.0) # Try to outbid Alex by a margin
        else:
            # If Alex bid moderately or low, still aim to outbid but with a smaller margin
            bid = max(bid, alex_prev_bid + 2.0)
    
    # Aggressive bidding if HP is low to ensure survival
    if my_status['hp'] <= 2:
        bid = max(bid, DAILY_SALARY * 0.95) # Bid very high when critically low on HP
    elif my_status['hp'] <= 4:
        bid = max(bid, DAILY_SALARY * 0.9) # Bid high when low on HP

    # Ensure bid does not exceed current budget
    bid = min(bid, my_status['budget'])

    # Ensure bid is at least a minimal positive value if budget allows and current bid is zero or negative
    if bid <= 0.0 and my_status['budget'] > 0:
        bid = 1.0 # Must bid something to potentially win if budget is available
    elif bid < 0.0: # If budget is zero or negative, bid 0
        bid = 0.0

    return bid
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

    # If no active opponents, bid minimally to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Default bid if no strong signals
    base_bid = DAILY_SALARY * 0.85 # 127.5

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP, almost dead
        base_bid = DAILY_SALARY * 1.15 # 172.5 - very aggressive
    elif my_status['hp'] <= 4: # Low HP
        base_bid = DAILY_SALARY * 1.05 # 157.5 - aggressive
    elif my_status['hp'] <= 6: # Moderate HP
        base_bid = DAILY_SALARY * 0.95 # 142.5

    # Adjust based on yesterday's highest bid from opponents
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest bid was very high, be prepared to exceed it
        if highest_prev_bid >= DAILY_SALARY * 0.9: # 135
            base_bid = max(base_bid, highest_prev_bid + 7.5)
        # If highest bid was moderate, match or slightly exceed
        elif highest_prev_bid >= DAILY_SALARY * 0.7: # 105
            base_bid = max(base_bid, highest_prev_bid + 2.5)
        # If highest bid was low, maybe we can save a bit, but still competitive
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.75) # 112.5

    # Consider supply: if very low, increase bid slightly
    supply = day_context['supply']
    if supply <= MIN_SUPPLY + 2: # e.g., 15, 16, 17
        base_bid += 5 # Add a small premium for very tight supply
    elif supply >= MAX_SUPPLY - 2: # e.g., 23, 24, 25
        # If supply is high, and my HP is good, try to be slightly less aggressive
        if my_status['hp'] > 6:
            base_bid = max(DAILY_SALARY * 0.7, base_bid - 5) # Minimum 105, or slightly reduce

    # Cap bid at budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure bid is at least 1.0 to participate if budget allows
    if final_bid <= 0 and my_status['budget'] > 0:
        return 1.0
    return max(1.0, final_bid)
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
    
    # If no opponents, bid a minimal amount to get water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid
    base_bid = DAILY_SALARY * 0.6 # A default moderate bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest bid was already very high, we might need to match or exceed
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, highest_prev_bid + 5.0) # Try to outbid
        else: # Otherwise, bid slightly above the highest previous bid
            base_bid = max(base_bid, highest_prev_bid + 1.0)
    
    # Adjust bid based on my HP or consecutive no-water days
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        base_bid = DAILY_SALARY * 0.95 # Bid very aggressively
    elif my_status['hp'] <= 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.8) # Bid aggressively

    # Adjust bid based on supply scarcity
    potential_water_units = int(day_context['supply'] // WATER_REQ)
    num_competitors = len(alive_opponents) + 1 # Me + alive opponents

    if potential_water_units < num_competitors:
        # Scarcity: competition is high, bid higher
        base_bid = max(base_bid, DAILY_SALARY * 0.75)
        if my_status['hp'] <= 5:
            base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif potential_water_units >= num_competitors + 1: # Abundant supply
        # Abundance: competition is low, can try to conserve budget
        base_bid = min(base_bid, DAILY_SALARY * 0.5)

    # Adjust bid based on day progression
    if day_context['day'] >= EPISODE_DAYS - 2: # Last few days, bid more aggressively to survive
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
        if my_status['hp'] <= 3:
            base_bid = DAILY_SALARY * 0.99 # Max out if critical on last days

    # Ensure bid doesn't exceed budget or is negative
    final_bid = min(my_status['budget'], base_bid)
    
    # Ensure bid is at least 1.0 to be considered a valid bid
    final_bid = max(1.0, final_bid)
    
    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQUIREMENT = 13
    MY_DAILY_SALARY = 150
    EPISODE_DAYS = 10 

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    eric_status = opponents_status.get("Eric")

    if not alive_opponents:
        return min(my_budget, MY_DAILY_SALARY * 0.4)

    remaining_days = EPISODE_DAYS - current_day + 1
    
    bid_multiplier = 0.8 
    
    if my_hp <= 2: 
        bid_multiplier = 0.98
    elif my_hp <= 4: 
        bid_multiplier = 0.9
    elif remaining_days <= 3 and my_hp < 10: 
        bid_multiplier = 0.95
    elif my_hp >= 8 and current_day > EPISODE_DAYS / 2: 
        bid_multiplier = 0.75
    
    my_target_bid = MY_DAILY_SALARY * bid_multiplier

    if current_supply <= MY_WATER_REQUIREMENT + 2: 
        my_target_bid = max(my_target_bid, MY_DAILY_SALARY * 0.9)
        if my_hp <= 4: 
            my_target_bid = MY_DAILY_SALARY * 0.99

    eric_prev_bid = 0
    eric_alive = False
    if eric_status and eric_status['alive']:
        eric_alive = True
        if eric_status.get('previous_trace'):
            eric_prev_bid = eric_status['previous_trace'].get('bid', 0)

    if eric_alive and eric_prev_bid > MY_DAILY_SALARY * 0.8: 
        if my_hp <= 3: 
            my_target_bid = max(my_target_bid, eric_prev_bid + 5)
        elif my_hp <= 6: 
            my_target_bid = max(my_target_bid, eric_prev_bid + 1)
        else: 
            my_target_bid = max(my_target_bid, eric_prev_bid * 0.98)

    final_bid = min(my_budget, my_target_bid)

    if my_budget < MY_DAILY_SALARY * 0.7 and my_hp < 10:
        final_bid = min(my_budget, MY_DAILY_SALARY * 0.99)

    if my_hp < 10 and final_bid < MY_DAILY_SALARY * 0.1:
        final_bid = min(my_budget, MY_DAILY_SALARY * 0.1)

    if remaining_days == 1 and my_hp < 10:
        final_bid = min(my_budget, MY_DAILY_SALARY * 1.0)

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
    num_alive_opponents = len(alive_opponents)
    
    if not alive_opponents:
        return max(1.0, min(my_status['budget'], DAILY_SALARY * 0.1))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.5 

    if my_status['hp'] <= 2:
        return max(1.0, min(my_status['budget'], DAILY_SALARY * 0.95))
    elif my_status['hp'] == 3:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                if day_context['supply'] / (num_alive_opponents + 1) > WATER_REQ * 1.5:
                    return max(1.0, min(my_status['budget'], DAILY_SALARY * 0.3))
                return max(1.0, min(my_status['budget'], DAILY_SALARY * 0.7))
            return max(1.0, min(my_status['budget'], DAILY_SALARY * 0.95))
        
        base_bid = max(base_bid, highest_prev_bid + 1.5)
    
    num_total_agents = num_alive_opponents + 1
    total_estimated_demand = num_total_agents * WATER_REQ
    
    if day_context['supply'] < total_estimated_demand:
        base_bid *= 1.15
    elif day_context['supply'] >= total_estimated_demand + WATER_REQ:
        base_bid *= 0.9
    
    if day_context['day'] > EPISODE_DAYS * 0.7:
        base_bid *= 1.1
    
    final_bid = max(1.0, min(my_status['budget'], base_bid))
    
    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From the meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no active opponents, bid low to save money
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid, adjusting for day and supply
    base_bid = DAILY_SALARY * 0.55 # Moderate default bid

    current_supply = day_context['supply']
    current_day = day_context['day']

    # If supply is tight (e.g., less than enough for me and one more, or just enough for me)
    # 13 (my req) + 13 (one opp req) = 26. Max supply is 25. So supply is often tight for two.
    # If supply is very low (e.g., only enough for 1-2 people)
    if current_supply <= WATER_REQ * 1.5: # If supply is less than 1.5x my requirement (e.g., <= 19.5)
        base_bid = DAILY_SALARY * 0.75
    
    # Aggressive bidding if HP is low or no_water_days > 0
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        base_bid = DAILY_SALARY * 0.95 # Prioritize survival
    elif my_status['hp'] <= 4: # Medium low HP
        base_bid = DAILY_SALARY * 0.7

    # Adjust bid based on highest opponent bid from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents bid high yesterday, react
        if highest_prev_bid >= DAILY_SALARY * 0.7: # If yesterday's highest was ~105 or more
            if my_status['hp'] <= 3: # Critical HP, need to win
                base_bid = max(base_bid, highest_prev_bid + 5.0) # Try to outbid
            else: # Healthy, but competitive
                base_bid = max(base_bid, highest_prev_bid * 0.95) # Stay close
        elif highest_prev_bid > DAILY_SALARY * 0.3: # Moderate previous bid
            base_bid = max(base_bid, highest_prev_bid + 1.0) # Slightly outbid

    # Cap bid at daily salary unless absolutely critical and budget allows
    final_bid = min(my_status['budget'], base_bid)
    
    # Ensure bid is not negative
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_HP = 10 # Assuming standard initial HP

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid conservatively to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine highest previous bid
    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Calculate number of available water units and potential competitors
    num_available_water_units = int(day_context['supply'] / WATER_REQ)
    num_competitors = len(alive_opponents) + 1 # Myself + alive opponents

    # Base bid initialization
    current_bid = DAILY_SALARY * 0.5 # A reasonable starting point

    # Strategy based on my HP
    if my_status['hp'] <= 2: # Critical HP: Must get water
        current_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP: Strong push for water
        current_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] < MAX_HP: # Not full, but not critical
        current_bid = DAILY_SALARY * 0.65
    else: # Full HP: Can afford to be more strategic
        current_bid = DAILY_SALARY * 0.5

    # Adjust bid based on highest previous opponent bid
    if highest_prev_bid > 0:
        # If my current bid is not enough to beat the highest previous bid, increase it
        if current_bid <= highest_prev_bid + 5: # Add a small margin
            current_bid = highest_prev_bid + 5
        # If I'm healthy and my bid is much higher than highest_prev_bid, try to save
        elif my_status['hp'] == MAX_HP and current_bid > highest_prev_bid + 10:
            current_bid = max(DAILY_SALARY * 0.4, highest_prev_bid + 1)

    # Adjust bid based on supply scarcity
    if num_available_water_units < num_competitors:
        # Water is scarce, competition is high. Increase bid.
        if my_status['hp'] <= 4: # If low HP, bid very aggressively
            current_bid = max(current_bid, DAILY_SALARY * 0.9)
        else: # If healthy, still need to compete
            current_bid = max(current_bid, DAILY_SALARY * 0.75)
    elif num_available_water_units >= num_competitors * 2:
        # Water is abundant. If healthy, try to win cheaply.
        if my_status['hp'] == MAX_HP:
            current_bid = min(current_bid, DAILY_SALARY * 0.4)
        else: # Even if not full HP, if water is abundant, no need to overbid
            current_bid = min(current_bid, DAILY_SALARY * 0.6)


    # Ensure bid does not exceed budget
    final_bid = min(current_bid, my_status['budget'])

    # Ensure bid is at least a small positive number if budget allows, to participate
    if final_bid <= 0 and my_status['budget'] > 0:
        final_bid = 0.1

    return final_bid
"""
