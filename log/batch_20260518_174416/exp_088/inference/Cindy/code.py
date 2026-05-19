# ============================================================
# Experiment: exp_088
# Agent: Cindy
# Source: exp_088
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Strategy 1: If I'm the only one left, bid minimum to conserve budget.
    if not alive_opponents:
        return min(my_status['budget'], 1)

    # Calculate total water demand and supply pressure
    total_water_demand = WATER_REQ # My requirement
    for opp in alive_opponents:
        total_water_demand += opp['water_requirement']
    
    current_supply = day_context['supply']

    # Determine a dynamic base bid multiplier based on supply pressure
    # This helps adjust bids even before looking at opponent's previous bids
    supply_pressure_multiplier = 0.55 # Default moderate bid multiplier
    if total_water_demand > 0:
        if current_supply < total_water_demand * 0.8: # Very tight supply
            supply_pressure_multiplier = 0.75
        elif current_supply < total_water_demand: # Tight supply
            supply_pressure_multiplier = 0.65
        elif current_supply > total_water_demand * 1.2: # Abundant supply
            supply_pressure_multiplier = 0.45
    
    # Base bid influenced by supply pressure
    dynamic_base_bid = DAILY_SALARY * supply_pressure_multiplier

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Strategy 2: Decision logic based on yesterday's highest pressure (if traces exist)
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If yesterday's highest bid was very aggressive (high competition)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # My HP is good, can take a calculated risk to conserve budget
                return min(my_status['budget'], max(dynamic_base_bid * 0.8, DAILY_SALARY * 0.4)) # Ensure it's not too low but still conserves
            else: # My HP is low, must secure water at almost any cost
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        
        # If yesterday's highest bid was moderate, adapt by bidding slightly above it
        # Ensure it's at least the dynamic_base_bid
        bid_from_prev_adaptive = max(dynamic_base_bid, highest_prev_bid + 1.5)
        
        # If I missed water yesterday, I need to be more aggressive
        if my_status['no_water_days'] >= 1:
            bid_from_prev_adaptive = max(bid_from_prev_adaptive, DAILY_SALARY * 0.75) # Significantly increase bid

        return min(my_status['budget'], bid_from_prev_adaptive)

    # Strategy 3: No yesterday's bids available (e.g., Day 1 or opponents didn't bid)
    if my_status['hp'] <= 2: # Critical HP, bid very high
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    elif my_status['no_water_days'] >= 1: # Missed water, be more aggressive
        return min(my_status['budget'], max(dynamic_base_bid, DAILY_SALARY * 0.7))
    
    # Default bid if no specific conditions met: use the dynamic_base_bid
    return min(my_status['budget'], dynamic_base_bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_bid = DAILY_SALARY * 0.6

    if my_status['hp'] <= 2:
        current_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5:
        current_bid = DAILY_SALARY * 0.8
    
    if my_status['no_water_days'] > 0:
        current_bid = max(current_bid, DAILY_SALARY * 0.9)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 5:
                current_bid = max(current_bid, highest_prev_bid + 1)
            else:
                current_bid = max(current_bid, highest_prev_bid + 5)
        else:
            current_bid = max(current_bid, highest_prev_bid + 2.5)

    final_bid = min(my_status['budget'], current_bid)

    if my_status['hp'] > 0 and my_status['budget'] > 0 and final_bid < 1.0:
        final_bid = 1.0

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
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    base_bid = DAILY_SALARY * 0.9

    # Adjust bid based on my HP
    HP_CRITICAL_THRESHOLD = 3
    HP_LOW_THRESHOLD = 5

    if my_hp <= HP_CRITICAL_THRESHOLD:
        base_bid = DAILY_SALARY * 1.15
    elif my_hp <= HP_LOW_THRESHOLD:
        base_bid = DAILY_SALARY * 1.05

    # Adjust bid based on opponent's previous day bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        if max_yesterday_bid >= DAILY_SALARY * 0.9:
            base_bid = max(base_bid, max_yesterday_bid + 5.0)
        elif max_yesterday_bid >= DAILY_SALARY * 0.7:
            base_bid = max(base_bid, max_yesterday_bid + 2.0)
        else:
            base_bid = min(base_bid, max_yesterday_bid + 10.0)

    # Adjust bid based on current supply
    if current_supply <= WATER_REQ + 2:
        base_bid = max(base_bid, DAILY_SALARY * 1.05)
    elif current_supply >= WATER_REQ * 1.5:
        base_bid = min(base_bid, DAILY_SALARY * 0.8)

    # Final constraints
    bid_amount = min(base_bid, my_budget)

    if bid_amount <= 0.0 and my_budget > 0.0:
        bid_amount = 1.0
    elif bid_amount <= 0.0:
        bid_amount = 0.0

    return bid_amount
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # 1. No active opponents: Bid minimal to conserve budget.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    # 2. Critical HP or missed water yesterday: Bid aggressively to survive.
    if my_status['no_water_days'] >= 1 or my_status['hp'] <= 2:
        # If it's the last day, bid everything if necessary
        if day_context['day'] == EPISODE_DAYS:
            return my_status['budget']
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # 3. Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Calculate number of water slots available
    supply = day_context['supply']
    num_slots = int(supply // WATER_REQ)

    # 4. Abundant supply: If there are enough slots for everyone (me + alive opponents)
    # and my HP is good, bid low to save budget.
    if num_slots >= (num_alive_opponents + 1) and my_status['hp'] > 3:
        # Try to bid slightly above a minimal value or lowest previous bid to ensure winning a slot.
        if yesterday_bids:
            # Bid slightly above the minimum of previous bids, but not too low
            min_prev_bid = min(yesterday_bids)
            return min(my_status['budget'], max(DAILY_SALARY * 0.25, min_prev_bid * 1.05))
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.3) # Default low bid

    # 5. Scarce/Moderate supply or not abundant, and not critical HP.
    # React to opponent's previous bids.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest previous bid was very high (e.g., > 80% of daily salary)
        # and my HP is not critical, consider if I can afford to lose or need to win.
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 5: # Good HP, can afford to lose a round or bid lower
                return min(my_status['budget'], DAILY_SALARY * 0.4)
            else: # Moderate HP, need water, bid aggressively but not max
                return min(my_status['budget'], DAILY_SALARY * 0.9)
        else: # Highest previous bid was moderate
            # Bid slightly above the highest previous bid to secure a slot
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
    
    # 6. Default bid if no previous bids (e.g., Day 1) and not critical HP
    # or if the above conditions don't apply.
    # Adjust based on perceived competition.
    if num_slots <= (num_alive_opponents + 1): # Competitive situation
        return min(my_status['budget'], DAILY_SALARY * 0.7)
    else: # Less competitive (more slots than current competitors, but not "abundant" by earlier check)
        return min(my_status['budget'], DAILY_SALARY * 0.55)
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

    # If no opponents are alive, bid a minimal amount to conserve budget.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from all alive opponents.
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid strategy based on my current health and water status.
    my_target_bid = 0.0

    # If HP is critical (2 or less) or I've gone without water, bid very aggressively.
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        my_target_bid = DAILY_SALARY * 0.95 # Highly aggressive bid (e.g., 142.5)
    else:
        # If HP is stable, bid competitively but with some budget consideration.
        my_target_bid = DAILY_SALARY * 0.75 # Moderately aggressive bid (e.g., 112.5)

    # Adjust bid based on yesterday's highest opponent bid to ensure competitive edge.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
            # When desperate, ensure to outbid the highest previous bid with a good margin.
            my_target_bid = max(my_target_bid, highest_prev_bid + 5.0)
        else:
            # When stable, aim to outbid, but be slightly more cautious if bids were extremely high.
            if highest_prev_bid >= DAILY_SALARY * 0.9:
                my_target_bid = max(my_target_bid, highest_prev_bid + 1.0) # Just edge them out
            else:
                my_target_bid = max(my_target_bid, highest_prev_bid + 2.5) # A small increment

    # Consider the day in the meta-round for end-game aggressiveness.
    # If it's near the end and I have a healthy budget, I can afford to be more aggressive.
    if day_context['day'] >= EPISODE_DAYS - 2 and my_status['budget'] > DAILY_SALARY:
        my_target_bid = max(my_target_bid, DAILY_SALARY * 1.0) # Bid full salary if needed

    # Ensure the final bid does not exceed the current budget.
    final_bid = min(my_status['budget'], my_target_bid)

    # Ensure a minimum bid if I need water (not full HP) to prevent bidding too low by mistake.
    if my_status['hp'] < 10 and final_bid < DAILY_SALARY * 0.2:
        final_bid = max(final_bid, DAILY_SALARY * 0.2) # Set a floor of 30 if not full HP

    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13
    
    # Base bid, assuming constant competition for the single full water slot
    bid = DAILY_SALARY * 0.9
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid a minimal amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1) 

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP, must win
        bid = max(bid, DAILY_SALARY * 1.15) # Bid very aggressively, above salary
        if max_yesterday_bid > 0:
            bid = max(bid, max_yesterday_bid + 10) # Outbid highest previous bid significantly
    elif my_status['hp'] <= 5: # Low HP, need water
        bid = max(bid, DAILY_SALARY * 1.05) # Bid high, slightly above salary
        if max_yesterday_bid > 0:
            bid = max(bid, max_yesterday_bid + 5) # Outbid highest previous bid
    else: # Healthy HP (my_status['hp'] > 5)
        # If healthy, maintain a strong competitive bid.
        bid = max(bid, DAILY_SALARY * 0.9) # Strong base bid
        if max_yesterday_bid > 0:
            # If opponents were very aggressive, match or slightly exceed to stay competitive.
            if max_yesterday_bid >= DAILY_SALARY * 0.9:
                bid = max(bid, max_yesterday_bid + 2)
            # If opponents were less aggressive, still bid strong, but maybe slightly less than salary to save.
            else:
                bid = max(bid, DAILY_SALARY * 0.85) # Still high enough to win against weak bids

    # Final bid must not exceed budget
    final_bid = min(my_status['budget'], bid)
    
    # Ensure a non-zero bid if water is needed and budget allows
    if my_status['budget'] > 0 and my_status['hp'] < 10: # If not full HP, we need water
        final_bid = max(final_bid, 1.0)
    elif my_status['budget'] > 0 and my_status['hp'] >= 10: # If full HP, can bid less to save
        final_bid = max(final_bid, 0.1) # A token bid if not critical, but still participate

    # If budget is extremely low and HP is critical, bid everything
    if my_status['budget'] < DAILY_SALARY * 0.5 and my_status['hp'] <= 3:
        final_bid = my_status['budget']

    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Strategy 1: Prioritize survival if health is critical or water was missed
    if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # Strategy 2: React to opponent's previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were bidding very high, I need to be competitive
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            # If relatively healthy, try to outbid slightly
            if my_status['hp'] > 5:
                base_bid = highest_prev_bid + 1.5
            # If not super healthy but not desperate, bid more aggressively
            else:
                base_bid = highest_prev_bid + 5.0
        
        # If opponents were bidding moderately, try to slightly outbid them
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            base_bid = highest_prev_bid + 1.0
        
        # If opponents were bidding low, I can bid moderately to save budget
        else:
            base_bid = DAILY_SALARY * 0.55
            
    else:
        # If no previous bids from opponents (e.g., Day 1 or all opponents died)
        # Bid a moderate amount to secure water while saving budget
        base_bid = DAILY_SALARY * 0.6

    # Ensure bid does not exceed budget and is at least 1 if I need water
    final_bid = min(my_status['budget'], base_bid)
    if my_status['budget'] > 0 and (my_status['hp'] <= 5 or my_status['no_water_days'] >= 1):
        final_bid = max(final_bid, 1.0) # Ensure a non-zero bid if somewhat desperate

    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Determine available water slots based on supply and my water requirement
    # With supply 15-24, only one player can get 13 water.
    # With supply 25, two players can get water (e.g., 13 and 12).
    available_water_slots = 1
    if day_context['supply'] >= WATER_REQ * 2 - 1: # 25 >= 13*2 - 1 = 25
        available_water_slots = 2

    # Base bid strategy
    base_bid = DAILY_SALARY * 0.5 # Default: 75

    # Adjust bid based on survival needs
    if my_status['hp'] <= 3: # Critical HP, bid very aggressively
        return min(my_status['budget'], DAILY_SALARY * 0.98)
    
    if my_status['no_water_days'] >= 1: # Haven't gotten water recently, need it
        return min(my_status['budget'], DAILY_SALARY * 0.9)

    # If competition is high (more alive opponents than water slots)
    if num_alive_opponents >= available_water_slots and available_water_slots > 0:
        base_bid = DAILY_SALARY * 0.65 # Increase base bid for tighter competition (97.5)
    
    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were very aggressive yesterday (bidding close to or above my salary)
        if highest_prev_bid >= DAILY_SALARY * 0.85: # 127.5
            if my_status['hp'] > 5 and available_water_slots > 1: # If HP is good and there's enough water for multiple
                return min(my_status['budget'], DAILY_SALARY * 0.7) # Try to get it cheaper (105)
            elif my_status['hp'] > 7: # If HP is very good, try to underspend a bit
                return min(my_status['budget'], highest_prev_bid * 0.9)
            else: # HP is not great or water is scarce, be more competitive
                return min(my_status['budget'], highest_prev_bid + 1.5) # Slightly outbid
        
        # If opponents were moderate, bid slightly above their highest
        return min(my_status['budget'], max(base_bid, highest_prev_bid + 1.5))

    # Fallback if no previous bids or other conditions apply
    return min(my_status['budget'], base_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid: moderate, assuming some competition
    bid_amount = DAILY_SALARY * 0.6

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP, bid very aggressively
        bid_amount = DAILY_SALARY * 0.98
    elif my_status['hp'] <= 5: # Low HP, bid aggressively
        bid_amount = DAILY_SALARY * 0.85

    # Analyze opponent's previous bids and total water demand
    yesterday_opponent_bids = []
    total_opponent_water_req = 0
    for opp in alive_opponents:
        total_opponent_water_req += opp['water_requirement']
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_opponent_bids.append(prev['bid'])

    total_demand = WATER_REQ + total_opponent_water_req

    # Competition analysis based on supply and previous bids
    if current_supply < total_demand: # Scarcity, competition is high
        if yesterday_opponent_bids:
            highest_prev_opp_bid = max(yesterday_opponent_bids)
            # React to high bidders like Alex
            if highest_prev_opp_bid >= DAILY_SALARY * 0.9:
                if my_status['hp'] > 5: # If not critical, match or slightly exceed
                    bid_amount = max(bid_amount, highest_prev_opp_bid + (DAILY_SALARY * 0.02))
                else: # Critical HP, go very high to secure water
                    bid_amount = max(bid_amount, highest_prev_opp_bid + (DAILY_SALARY * 0.05))
            elif highest_prev_opp_bid >= DAILY_SALARY * 0.7: # Moderate bidders like David
                bid_amount = max(bid_amount, highest_prev_opp_bid + (DAILY_SALARY * 0.03))
            else: # Low bidders like Bob/Eric, just bid slightly above
                bid_amount = max(bid_amount, highest_prev_opp_bid + (DAILY_SALARY * 0.01))
        # If no previous bids, but scarcity, assume moderate competition
        elif num_alive_opponents > 0:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.7)
    else: # Enough water for everyone, bid lower unless HP is critical
        if my_status['hp'] > 5: # If HP is good, conserve budget
            bid_amount = min(bid_amount, DAILY_SALARY * 0.4)

    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], bid_amount)

    # Ensure bid is at least 1.0 to participate
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    # --- Bidding thresholds based on my status ---
    base_bid = DAILY_SALARY * 0.5
    low_hp_bid = DAILY_SALARY * 0.8
    critical_hp_bid = DAILY_SALARY * 0.95
    no_water_penalty_per_day = DAILY_SALARY * 0.08

    # Calculate current bid based on my status
    current_bid = base_bid

    if my_status['no_water_days'] > 0:
        current_bid += my_status['no_water_days'] * no_water_penalty_per_day

    if my_status['hp'] <= 3:
        current_bid = max(current_bid, low_hp_bid)
    if my_status['hp'] <= 1:
        current_bid = max(current_bid, critical_hp_bid)

    # Adjust bid based on supply context
    # If supply is very low, we might need to bid more aggressively
    if day_context['supply'] < WATER_REQ * 1.5: # If supply is less than 1.5 times my requirement, it's very tight for me alone.
        current_bid += DAILY_SALARY * 0.1
    elif day_context['supply'] < WATER_REQ * (len([o for o in opponents_status.values() if o['alive']]) + 1) * 0.8: # If supply is tight for everyone
        current_bid += DAILY_SALARY * 0.05

    # --- React to opponents' previous bids ---
    yesterday_bids = []
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents were bidding very high yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 3:
                current_bid = max(current_bid, highest_prev_bid * 0.9)
            else:
                current_bid = max(current_bid, highest_prev_bid * 1.05 + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
             current_bid = max(current_bid, avg_prev_bid * 1.05)
        else:
             current_bid = max(current_bid, avg_prev_bid * 0.95)

    # Ensure bid is at least a minimum to be considered
    current_bid = max(1.0, current_bid)

    # Ensure bid does not exceed budget
    current_bid = min(my_status['budget'], current_bid)

    # Cap the bid if not in critical condition to avoid overspending
    if my_status['hp'] > 1:
        current_bid = min(current_bid, DAILY_SALARY * 1.2)

    return current_bid
"""
