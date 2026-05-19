# ============================================================
# Experiment: exp_095
# Agent: Cindy
# Source: exp_095
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    BID_INCREMENT_CRITICAL = 1.0
    BID_INCREMENT_NORMAL = 0.1
    DESPERATE_HP_THRESHOLD = 2
    DESPERATE_NO_WATER_DAYS = 1

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid a low amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Assess my state
    is_desperate = my_status['no_water_days'] >= DESPERATE_NO_WATER_DAYS or my_status['hp'] <= DESPERATE_HP_THRESHOLD

    # Assess market state
    total_water_demand = WATER_REQ + sum(o['water_requirement'] for o in alive_opponents)
    supply = day_context['supply']
    is_supply_tight = supply < total_water_demand

    # Formulate initial bid based on my state and market tightness
    if is_desperate:
        my_bid = DAILY_SALARY * 0.95 # Bid very high if desperate
    elif is_supply_tight:
        my_bid = DAILY_SALARY * 0.7 # Higher than normal if supply is tight, but not desperate
    else:
        my_bid = DAILY_SALARY * 0.5 # Normal bid, can be lower if competition is low

    # Adjust based on opponent's previous bids
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        if is_desperate or is_supply_tight:
            # Ensure I outbid if critical (desperate or supply is tight)
            my_bid = max(my_bid, max_yesterday_bid + BID_INCREMENT_CRITICAL)
        else:
            # Slightly outbid if not critical, but keep a reasonable floor
            my_bid = max(my_bid, max_yesterday_bid + BID_INCREMENT_NORMAL)
        
    # Ensure a minimum bid even if yesterday's bids were very low or non-existent
    # This floor ensures I attempt to get water for my requirement
    my_bid = max(my_bid, DAILY_SALARY * 0.4)

    # Final bid constraints
    my_bid = min(my_bid, my_status['budget']) # Never bid more than I have
    my_bid = max(my_bid, 1.0) # Ensure bid is at least 1.0

    return my_bid
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid = 0.0 # Initialize bid

    # Prioritize survival
    if my_status['no_water_days'] >= 1 or my_status['hp'] <= 2:
        bid = DAILY_SALARY * 0.95 # Critical state, bid very aggressively
    elif my_status['hp'] <= 4:
        bid = DAILY_SALARY * 0.8  # Low HP, bid higher
    else:
        bid = DAILY_SALARY * 0.5  # Healthy HP, start with a moderate bid

    # Adjust bid based on yesterday's highest bid from active opponents
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest previous bid was very high (reflecting Bob-like behavior)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] <= 4 or my_status['no_water_days'] >= 1:
                bid = max(bid, highest_prev_bid + 5.0) # If vulnerable, must outbid significantly
            else:
                # If healthy, still need to compete, but can be slightly less aggressive if supply allows
                if day_context['supply'] <= MIN_SUPPLY + 2: # Very tight supply
                     bid = max(bid, highest_prev_bid + 3.0)
                else:
                     bid = max(bid, highest_prev_bid + 1.0)
        # If highest previous bid was moderate (reflecting Eric-like behavior)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            bid = max(bid, highest_prev_bid + 1.0) # Try to outbid slightly to win
        # If highest previous bid was low (reflecting Alex/David-like behavior)
        else:
            bid = max(bid, highest_prev_bid + 0.5) # Bid slightly above to secure water and save budget
    
    # Adjust bid based on day in episode (end game pressure)
    if day_context['day'] > EPISODE_DAYS * 0.7: # Last 30% of days
        bid = max(bid, DAILY_SALARY * 0.7) # Increase urgency

    # Adjust bid based on supply
    if day_context['supply'] <= MIN_SUPPLY + 2: # Very low supply, high competition
        bid = max(bid, DAILY_SALARY * 0.75) # Ensure aggressive bid
    elif day_context['supply'] >= MAX_SUPPLY - 2: # Very high supply, potentially less competition
        if my_status['hp'] > 5 and my_status['no_water_days'] == 0:
            bid = min(bid, DAILY_SALARY * 0.6) # If healthy and ample supply, try to save a bit

    # Ensure bid is not negative and within budget
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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Collect yesterday's bids and identify Eric's status
    yesterday_bids = []
    eric_prev_bid = 0
    eric_budget = 0
    eric_is_alive = False

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
        if opp['agent_id'] == 'Eric':
            eric_is_alive = True
            eric_prev_bid = prev.get('bid', 0)
            eric_budget = opp['budget']

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid: a safe starting point
    bid = DAILY_SALARY * 0.55

    # Strategy based on my HP and game state
    if my_hp <= 2: # Critical HP, must get water
        bid = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP, prioritize getting water
        bid = DAILY_SALARY * 0.8
    elif current_day >= EPISODE_DAYS - 1: # Last day or second to last, ensure survival
        if my_hp < (EPISODE_DAYS - current_day + 1): # Not enough HP to survive remaining days
            return my_budget # Bid everything

    # React to Eric's behavior using previous_trace
    if eric_is_alive and eric_prev_bid > DAILY_SALARY: # Eric bid very high yesterday
        if eric_budget < DAILY_SALARY * 0.75 and eric_prev_bid > 0: # Eric's budget is low, but he's aggressive
            # He might be desperate. Try to outbid him efficiently.
            if my_hp <= 5:
                bid = max(bid, eric_prev_bid * 0.8 + 1)
            else:
                bid = max(bid, DAILY_SALARY * 0.6)
        elif eric_budget > DAILY_SALARY * 2: # Eric has plenty of budget, he can sustain high bids
             if my_hp <= 4: # Need water, must compete strongly
                 bid = max(bid, eric_prev_bid * 0.9 + 5)
             else: # Good HP, let him spend, but stay competitive
                 bid = max(bid, DAILY_SALARY * 0.7)

    # General reaction to the highest previous bid if not specifically handled by Eric's high bid
    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.8: # High competition from others
            if my_hp <= 3:
                bid = max(bid, highest_prev_bid + 5)
            else:
                bid = max(bid, highest_prev_bid * 0.9)
        else: # Moderate competition
            bid = max(bid, highest_prev_bid + 1)

    # Adjust bid based on supply scarcity
    estimated_total_demand = WATER_REQ
    for opp in alive_opponents:
        estimated_total_demand += opp['water_requirement']

    if current_supply < estimated_total_demand: # Supply is tight, competition will be higher
        if my_hp <= 5:
            bid = max(bid, DAILY_SALARY * 0.8)
        else:
            bid = max(bid, DAILY_SALARY * 0.6)
    elif current_supply > estimated_total_demand + WATER_REQ * 2: # Supply is very abundant, can save money
        bid = min(bid, DAILY_SALARY * 0.3)

    # Final bid cannot exceed current budget and must be positive
    final_bid = min(my_budget, bid)
    final_bid = max(0.01, final_bid)

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

    total_water_needed = WATER_REQ
    for opp in alive_opponents:
        total_water_needed += opp['water_requirement']

    is_scarce = current_supply < total_water_needed

    base_bid = DAILY_SALARY * 0.5

    if my_hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif my_hp <= 4:
        base_bid = DAILY_SALARY * 0.75
    elif my_hp >= 8:
        base_bid = DAILY_SALARY * 0.4

    if is_scarce:
        base_bid *= 1.2
        if my_hp <= 3:
            base_bid = DAILY_SALARY * 0.95

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace')
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)

        if max_yesterday_bid > DAILY_SALARY * 0.7:
            if my_hp <= 3:
                base_bid = max(base_bid, max_yesterday_bid + 5)
            else:
                base_bid = max(base_bid, avg_yesterday_bid * 1.05)
        elif max_yesterday_bid < DAILY_SALARY * 0.3:
            if my_hp >= 8:
                base_bid = min(base_bid, avg_yesterday_bid + 5)
            else:
                base_bid = max(base_bid, DAILY_SALARY * 0.4)

    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_hp <= 5:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    if remaining_days == 1 and my_hp <= 2:
        base_bid = DAILY_SALARY * 0.99

    calculated_bid = base_bid

    if my_no_water_days > 0:
        calculated_bid = max(calculated_bid, DAILY_SALARY * 1.1)

    final_bid = min(my_budget, calculated_bid)

    if final_bid < 1 and my_budget >= 1:
        final_bid = 1
    elif final_bid < 1 and my_budget < 1:
        final_bid = my_budget

    return round(final_bid, 2)
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

    # If no opponents, bid minimum to get water
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.1))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid strategy
    current_bid = DAILY_SALARY * 0.5 # A moderate starting point

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # Adjust bid based on my HP and opponent's previous actions
        if my_status['hp'] <= 2: # Critical HP, need water to survive
            # Bid aggressively, slightly above the highest previous bid or a high percentage of salary
            current_bid = max(highest_prev_bid * 1.05, DAILY_SALARY * 0.9)
        elif my_status['hp'] <= 4: # Low HP, but not critical
            # Bid to secure water, but try to save a bit
            current_bid = max(avg_prev_bid * 1.02, DAILY_SALARY * 0.7)
        else: # Healthy HP, can afford to be more strategic and save budget
            # If supply is very tight, might still need to bid higher
            # Check if supply is less than what I need + what at least one other opponent needs
            if day_context['supply'] < WATER_REQ * (num_alive_opponents + 0.5): # Not enough for everyone easily
                current_bid = max(avg_prev_bid * 0.9, DAILY_SALARY * 0.6) # Still competitive
            else: # Supply is more abundant, try to save
                current_bid = DAILY_SALARY * 0.4 # More conservative bid

        # If previous bids were generally very high, indicating high pressure, react
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 3: # If healthy, maybe don't jump into a bidding war
                current_bid = min(current_bid, DAILY_SALARY * 0.65)
            else: # If low HP, must compete
                current_bid = max(current_bid, highest_prev_bid + 2.0)
    else: # No prior bids from alive opponents, use a default strategy
        if my_status['hp'] <= 2:
            current_bid = DAILY_SALARY * 0.9
        elif my_status['hp'] <= 4:
            current_bid = DAILY_SALARY * 0.7
        else:
            current_bid = DAILY_SALARY * 0.5

    # Ensure bid is at least a minimal amount to be considered
    min_viable_bid = 1.0
    
    # Final check: Ensure bid does not exceed budget and is not negative
    final_bid = max(min_viable_bid, min(my_status['budget'], current_bid))

    # For critical HP (1 or less), bid almost everything to survive
    if my_status['hp'] <= 1:
        final_bid = my_status['budget'] * 0.99
    
    return float(final_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQUIREMENT = 13
    MY_DAILY_SALARY = 150
    EPISODE_DAYS = 10

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid strategy: Start with a competitive bid, around 65% of daily salary
    base_bid = MY_DAILY_SALARY * 0.65

    # Emergency bids (prioritize survival)
    if my_no_water_days > 0 or my_hp <= 2:
        # Critical state: bid very high to ensure water
        bid = MY_DAILY_SALARY * 0.95
    elif my_hp <= 4:
        # Low HP, need to recover aggressively
        bid = MY_DAILY_SALARY * 0.85
    else:
        bid = base_bid

    # Analyze opponents' previous bids to react
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were aggressive yesterday, increase bid to stay competitive
        if highest_prev_bid >= MY_DAILY_SALARY * 0.8: # e.g., highest bid was 120 or more
            bid = max(bid, highest_prev_bid + 5)
        elif highest_prev_bid >= MY_DAILY_SALARY * 0.6: # e.g., highest bid was 90 or more
            bid = max(bid, highest_prev_bid + 2)
        else:
            bid = max(bid, highest_prev_bid + 1) # Just slightly above low bids

    # Adjust based on supply and number of competitors
    # Estimate total water needed if everyone wanted their requirement
    total_water_needed_by_all = MY_WATER_REQUIREMENT * (num_alive_opponents + 1)
    
    if supply < total_water_needed_by_all: # High competition scenario
        bid *= 1.05 # Increase bid slightly
    elif supply > total_water_needed_by_all + MY_WATER_REQUIREMENT: # Plenty of water, can try to conserve
        bid *= 0.95 # Decrease bid slightly

    # Final adjustments
    # Ensure bid does not exceed current budget
    bid = min(my_budget, bid)
    # Ensure bid is at least 1 to participate
    bid = max(1, bid)

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

    current_day = day_context['day']
    current_supply = day_context['supply']

    # Base bid: Default competitive bid
    bid = DAILY_SALARY * 0.55 # 82.5

    # Track alive opponents and their previous bids/states
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid low to save money
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3) # 45

    yesterday_bids = []
    desperate_opponents_bidding_high = False
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
        
        # Check if any opponent is desperate (low HP or no water) and has budget to bid high
        if (opp['hp'] <= 2 or opp['no_water_days'] > 0) and opp['budget'] > DAILY_SALARY * 0.8:
            desperate_opponents_bidding_high = True

    # Adjust bid based on my HP and no_water_days
    if my_status['hp'] <= 2: # Critical HP
        bid = DAILY_SALARY * 0.95 # 142.5
    elif my_status['hp'] <= 4: # Low HP
        bid = max(bid, DAILY_SALARY * 0.8) # 120
    elif my_status['no_water_days'] > 0: # Missed water yesterday
        bid = max(bid, DAILY_SALARY * 0.7) # 105

    # Adjust bid based on supply
    if current_supply <= WATER_REQ + 5: # Low supply (e.g., 15-18 for 13 units), high competition
        bid = max(bid, DAILY_SALARY * 0.75) # 112.5
    elif current_supply >= 22: # High supply (e.g., 22-25)
        # If I'm not desperate, try to conserve
        if my_status['hp'] > 4 and my_status['no_water_days'] == 0:
            bid = min(bid, DAILY_SALARY * 0.4) # 60
        else: # Still need water, but supply is good, so less aggressive
            bid = min(bid, DAILY_SALARY * 0.65) # 97.5

    # Factor in previous bids from opponents
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.85: # Opponents were very aggressive
            if my_status['hp'] > 4 and my_status['no_water_days'] == 0: # If relatively healthy
                # Can afford to back off slightly to conserve budget
                bid = min(bid, DAILY_SALARY * 0.45) # 67.5
            else:
                # I need water, so I must compete
                bid = max(bid, highest_prev_bid + 5) # Try to outbid
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderately aggressive
            bid = max(bid, highest_prev_bid + 2) # Slightly outbid

    # If many opponents are desperate, increase bid as competition will be high
    if desperate_opponents_bidding_high:
        bid = max(bid, DAILY_SALARY * 0.88) # 132

    # End game strategy
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last 2 days
        if my_status['hp'] <= 3: # Must survive
            bid = max(bid, DAILY_SALARY * 0.98) # 147
        elif my_status['budget'] < DAILY_SALARY * 1.5 and my_status['hp'] > 5: # Conserve if healthy but low budget
            bid = min(bid, my_status['budget'] / (remaining_days + 1)) # Try to stretch budget

    # Ensure bid does not exceed budget
    final_bid = min(bid, my_status['budget'])

    # Ensure a positive bid if budget allows to be competitive
    final_bid = max(final_bid, 1.0)

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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimally to secure water cheaply
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Base bidding strategy based on health and need
    if my_hp <= 2 or my_no_water_days > 0:
        # Critical state: bid very aggressively to survive
        bid = DAILY_SALARY * 1.4
    elif my_hp <= 4:
        # Low HP: bid aggressively
        bid = DAILY_SALARY * 1.15
    else:
        # Healthy HP: bid competitively
        bid = DAILY_SALARY * 0.95

    # Adjust bid based on opponent's previous behavior
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were generally aggressive (bid > 80% of my salary)
        if highest_prev_bid > DAILY_SALARY * 0.8:
            # If I'm vulnerable (low HP or missed water), try to outbid them
            if my_hp <= 4 or my_no_water_days > 0:
                bid = max(bid, highest_prev_bid + 5)
            else:
                # If healthy, stay competitive but don't blindly overspend on extreme bids
                # Cap healthy aggression at 120% of daily salary, or slightly above highest_prev_bid
                bid = max(bid, min(highest_prev_bid + 1, DAILY_SALARY * 1.2))
        
    # Final day logic: if it's the last day and I need water to survive, bid all remaining budget
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days == 0 and my_hp <= 1:
        return my_budget

    # Ensure bid does not exceed current budget
    final_bid = min(bid, my_budget)

    # Ensure a positive minimum bid
    final_bid = max(final_bid, 1.0)
    
    # Cap the bid to a reasonable maximum if not in a critical last-day survival scenario
    # This prevents overspending on outlier opponent bids early in the game.
    if final_bid > DAILY_SALARY * 1.5 and remaining_days > 0:
        final_bid = DAILY_SALARY * 1.5

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

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to secure water (e.g., 1 credit)
    if not alive_opponents:
        return min(my_budget, 1.0)

    # Calculate days remaining
    days_remaining = EPISODE_DAYS - current_day + 1

    # Determine pressure based on my HP
    # If HP is very low, I MUST get water. Bid aggressively.
    if my_hp <= 2: # Critical HP
        return min(my_budget, DAILY_SALARY * 1.1) # Bid more than daily salary to ensure win
    elif my_hp <= 4: # Low HP
        return min(my_budget, DAILY_SALARY * 0.9)
    elif my_no_water_days > 0 and current_day > 1: # Missed water yesterday, need to recover
        return min(my_budget, DAILY_SALARY * 0.8)

    # Analyze opponent's previous bids for the current episode
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Base bid: A portion of daily salary. 
    # Since only one can win, we need to be competitive.
    base_bid = DAILY_SALARY * 0.6

    # Adjust bid based on observed competition
    if num_alive_opponents > 0:
        if max_yesterday_bid > 0:
            # Try to outbid the highest bid from yesterday by a small margin.
            competitive_bid = max_yesterday_bid + 5.0 # Add a small buffer
            if competitive_bid > DAILY_SALARY * 1.2: # Cap aggressive bids to avoid overspending too much
                competitive_bid = DAILY_SALARY * 1.2
            base_bid = max(base_bid, competitive_bid)
        else:
            # If no previous bids, or all bids were 0, assume moderate competition.
            # Bid a bit higher than a safe default to establish presence.
            base_bid = max(base_bid, DAILY_SALARY * 0.65)

    # Adjust for remaining days - Late game aggression
    # If it's late in the game, and I have budget, I can be more aggressive.
    if days_remaining <= 3 and my_hp < 10: # Late game, not full HP
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif days_remaining <= 2 and my_hp < 10:
        base_bid = max(base_bid, DAILY_SALARY * 1.0) # Bid full salary
    elif days_remaining == 1: # Last day, go all in if needed
        base_bid = my_budget # Bid everything if it's the last day and I need water

    # Ensure bid doesn't exceed budget
    final_bid = min(my_budget, base_bid)

    # Ensure bid is at least 1.0 to be a valid bid, unless budget is 0.
    return max(1.0, final_bid) if my_budget > 0 else 0.0
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
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    current_bid = DAILY_SALARY * 0.65

    if my_status['hp'] <= 2:
        current_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        current_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] >= 8 and my_status['budget'] > DAILY_SALARY * 2:
        current_bid = DAILY_SALARY * 0.55

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        if max_yesterday_bid > DAILY_SALARY * 0.7:
            if my_status['hp'] <= 5:
                current_bid = max(current_bid, max_yesterday_bid * 1.05)
            else:
                current_bid = max(current_bid, max_yesterday_bid * 0.9)
        
        if my_status['hp'] <= 3:
            avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)
            current_bid = max(current_bid, avg_yesterday_bid + 5)
            
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] <= 5:
        current_bid = max(current_bid, DAILY_SALARY * 1.1)

    min_necessary_bid = 1
    if my_status['hp'] <= 3:
        min_necessary_bid = DAILY_SALARY * 0.5

    final_bid = min(my_status['budget'], max(min_necessary_bid, current_bid))

    return final_bid
"""
