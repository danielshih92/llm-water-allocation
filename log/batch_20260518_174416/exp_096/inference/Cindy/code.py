# ============================================================
# Experiment: exp_096
# Agent: Cindy
# Source: exp_096
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
    supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid: A reasonable amount to secure water without overspending
    base_bid = DAILY_SALARY * 0.4

    # Calculate how many "full" water requirements can be met from supply
    # CRITICAL INDEX RULE: supply is float, ensure int conversion for operations
    available_water_units = int(supply // WATER_REQ)

    # Strategy 1: No opponents left, bid minimum to get water and save budget
    if num_alive_opponents == 0:
        return min(my_budget, 1)

    # Strategy 2: Critical HP, prioritize survival at almost any cost
    if my_hp <= 2:
        # Bid very high to ensure water, up to budget
        return min(my_budget, DAILY_SALARY * 0.95)

    # Strategy 3: No water available for anyone (supply < WATER_REQ)
    # This implies available_water_units will be 0.
    if available_water_units == 0:
        # Conserve budget if water is impossible to get
        return min(my_budget, 1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Strategy 4: General competitive scenario
    # Given WATER_REQ=13 and supply_range=[15, 25], available_water_units will always be 1
    # when supply is sufficient (>= 13). This means it's always a highly competitive scenario
    # where only one agent can get their full water requirement.
    
    # Adjust bid based on opponent's previous aggression
    if highest_prev_bid >= DAILY_SALARY * 0.7: # Opponents are very aggressive
        # Bid slightly above their high bid to secure water
        bid_amount = highest_prev_bid + 5
        bid_amount = max(bid_amount, DAILY_SALARY * 0.8) # Ensure a strong bid
        return min(my_budget, bid_amount)
    elif highest_prev_bid >= DAILY_SALARY * 0.4: # Opponents are moderately aggressive
        # Bid slightly above to win, but don't overpay too much
        bid_amount = max(base_bid + 5, highest_prev_bid + 1)
        bid_amount = min(bid_amount, DAILY_SALARY * 0.7) # Cap it to conserve budget if possible
        return min(my_budget, bid_amount)
    else: # Opponents bid low or no history
        # Be assertive but not wasteful. A moderate bid is needed due to high competition.
        return min(my_budget, DAILY_SALARY * 0.6)

    # Fallback, though all paths should return a bid
    return min(my_budget, base_bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_supply = day_context['supply']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_bidders = len(alive_opponents) + 1 # Me + alive opponents

    # Default bid if no specific conditions apply
    bid = DAILY_SALARY * 0.5

    # If no opponents, bid minimally to secure water and save budget
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # --- Adjust bid based on my health and need ---
    if my_hp <= 2: # Critical HP, bid aggressively
        bid = DAILY_SALARY * 0.95
    elif my_hp <= 5: # Low HP, bid high
        bid = DAILY_SALARY * 0.8
    elif my_status['no_water_days'] >= 1: # Missed water yesterday, need to secure it today
        bid = DAILY_SALARY * 0.9
    elif my_hp >= 8 and my_budget > DAILY_SALARY * 3: # Healthy and rich, can afford to be more conservative
        bid = DAILY_SALARY * 0.45

    # --- Adjust bid based on opponent's yesterday's behavior (previous_trace) ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents were highly aggressive yesterday, respond accordingly
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_hp <= 5: # I need water, must compete
                bid = max(bid, highest_prev_bid + 5)
            else: # I'm healthier, can try to slightly undercut or match
                bid = max(bid, highest_prev_bid * 0.95) # Still competitive but try to save
        # If opponents were generally conservative, don't overbid
        elif average_prev_bid < DAILY_SALARY * 0.4:
            if my_hp > 7: # Healthy, can save money
                bid = min(bid, average_prev_bid * 1.1)
            else: # Still need water, but don't go too high
                bid = max(bid, DAILY_SALARY * 0.4)
        
        # General adjustment: if my current bid is much lower than max_prev_bid, but I need water, raise it
        if my_hp <= 6 and bid < highest_prev_bid * 0.9:
            bid = max(bid, highest_prev_bid * 0.95)


    # --- Adjust bid based on current supply scarcity ---
    # Approximate water needed by all active players
    total_water_demand = WATER_REQ * num_alive_bidders
    
    if current_supply < total_water_demand * 0.8: # Very tight supply
        if my_hp <= 7: # Need water, bid more aggressively
            bid = max(bid, DAILY_SALARY * 0.8)
        else: # Healthy, still need to be competitive
            bid = max(bid, DAILY_SALARY * 0.65)
    elif current_supply >= total_water_demand * 1.5: # Abundant supply
        if my_hp > 8: # Healthy, can afford to bid lower
            bid = min(bid, DAILY_SALARY * 0.35)
        else: # Still need water, but can save a bit
            bid = min(bid, DAILY_SALARY * 0.45)

    # Final constraint: bid cannot exceed current budget
    final_bid = min(my_budget, bid)

    # Ensure bid is non-negative
    final_bid = max(0.0, final_bid)

    # If the calculated bid is zero but budget allows, make a minimal bid
    if final_bid == 0.0 and my_budget > 0:
        final_bid = min(my_budget, DAILY_SALARY * 0.05)
        
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
    
    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    days_remaining = EPISODE_DAYS - current_day + 1

    base_bid = DAILY_SALARY / 2 

    if my_hp <= 2 or my_no_water_days > 0:
        base_bid = DAILY_SALARY * 0.95 
    elif my_hp <= 5:
        base_bid = DAILY_SALARY * 0.7 
    elif days_remaining <= 2 and my_hp < 10:
        base_bid = DAILY_SALARY * 0.8
    
    if my_budget < base_bid and my_hp > 5:
        base_bid = max(1.0, my_budget * 0.75)
    elif my_budget < base_bid and (my_hp <= 5 or my_no_water_days > 0):
        base_bid = max(1.0, my_budget)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_hp > 3:
                base_bid = max(base_bid, highest_prev_bid * 0.9) 
            else:
                base_bid = max(base_bid, highest_prev_bid + 5)
        elif highest_prev_bid > DAILY_SALARY * 0.3:
            if current_supply < (WATER_REQ * (num_alive_opponents + 1) * 1.2):
                 base_bid = max(base_bid, highest_prev_bid + 1)
            else:
                 base_bid = min(base_bid, highest_prev_bid * 0.9)
        else:
            if my_hp < 8 and days_remaining > 3:
                base_bid = max(base_bid, DAILY_SALARY * 0.4)
            else:
                base_bid = min(base_bid, DAILY_SALARY * 0.3)

    final_bid = min(my_budget, base_bid)
    
    if my_budget > 0 and final_bid < 1.0 and (my_hp < 10 or my_no_water_days > 0):
        final_bid = 1.0
    
    if num_alive_opponents == 0:
        final_bid = min(my_budget, DAILY_SALARY * 0.1)
    
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Calculate remaining days
    remaining_days = EPISODE_DAYS - current_day

    # --- Determine base bid based on my status ---
    # Default bid: moderate, slightly above average to be competitive
    bid_factor = 0.55 

    # Increase bid if HP is low
    if my_hp <= 2: # Critical HP
        bid_factor = 0.98 # Very aggressive
    elif my_hp <= 4: # Low HP
        bid_factor = 0.85
    elif my_hp <= 6 and remaining_days <= 3: # End game pressure, moderate HP
        bid_factor = 0.75
    elif my_hp <= 8 and remaining_days <= 2: # Very late game, still need water
        bid_factor = 0.8

    my_calculated_bid = DAILY_SALARY * bid_factor

    # --- Adjust bid based on opponents' previous behavior ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # High competition threshold (e.g., opponents bidding very aggressively)
        if highest_prev_bid >= DAILY_SALARY * 0.85: 
            # If healthy AND not in the end-game, consider conserving
            if my_hp > int(EPISODE_DAYS * 0.7) and remaining_days > 2: 
                my_calculated_bid = min(my_calculated_bid, DAILY_SALARY * 0.35) # Conserve
            else: # Low HP or end-game, must win
                my_calculated_bid = max(my_calculated_bid, highest_prev_bid + 5.0) # Aggressive bid to ensure win
        else: # Moderate competition
            # Ensure my bid is at least slightly above average, or my base aggressive bid
            avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)
            my_calculated_bid = max(my_calculated_bid, avg_prev_bid + 2.0)

    # --- Special cases ---
    # If no opponents, bid very low but enough to get water if needed
    if num_alive_opponents == 0:
        if my_hp < EPISODE_DAYS: # If not full HP, still need water
            return min(my_budget, DAILY_SALARY * 0.15)
        return min(my_budget, DAILY_SALARY * 0.05) # Full HP, just conserve

    # Ensure bid is at least a minimal amount and does not exceed budget
    final_bid = max(1.0, my_calculated_bid)
    return min(my_budget, final_bid)
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

    # 1. If no active opponents, bid minimally to save budget.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # 2. Critical HP / No water for days: Prioritize survival. Bid aggressively.
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # 3. Collect yesterday's bids from active opponents' previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace')
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # Base bid if no relevant yesterday bids or as a fallback
    base_bid = DAILY_SALARY * 0.55 # A moderate default bid

    # 4. Decision logic based on yesterday's highest pressure and my status
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # Threshold for high bids (from example strategy)
        high_bid_threshold = DAILY_SALARY * 0.85

        if highest_prev_bid >= high_bid_threshold:
            # Opponents are bidding very high
            if my_status['hp'] > 3: # My HP is good, can afford to be less aggressive
                # Conserve budget, but still aim to be competitive (e.g., 60% of salary)
                return min(my_status['budget'], DAILY_SALARY * 0.6)
            else: # My HP is moderate/low, need to secure water aggressively
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else:
            # Opponents' highest bid was moderate or low
            # Bid slightly above it to secure water, ensuring it's at least the base bid.
            return min(my_status['budget'], max(base_bid, highest_prev_bid + 1.5))
    
    # Fallback if no yesterday bids (e.g., Day 1, or all opponents bid 0)
    return min(my_status['budget'], base_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid a minimal amount to save budget
    if not alive_opponents:
        return min(my_status['budget'], 1.0) # Bid 1.0 to ensure water if available

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        # Ensure 'bid' exists and is not None before adding
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # If there are yesterday's bids, react to the highest one
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # Aggressive bidding threshold (e.g., 85% of daily salary)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If my HP is good, I can afford to save money, let opponents overbid
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            # If my HP is low, I must get water, so bid very aggressively
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        else:\n            # If highest bid is moderate, bid slightly above it to win, but not too much
            # Ensure bid is at least a moderate amount (e.g., 50% of daily salary)
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
    
    # If no previous bids (e.g., first day or opponents didn't bid), bid based on own HP
    if my_status['hp'] <= 2:
        # Critical HP, bid high to survive
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    
    # Normal HP, bid moderately
    return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    # Identify strong and weak opponents based on historical meta-round context
    strong_opponents_ids = ["Alex", "Eric"]
    weak_opponents_ids = ["Bob", "David"]

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid a minimal amount to save budget
    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    strong_opponent_bids_yesterday = []

    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
                if opp_id in strong_opponents_ids:
                    strong_opponent_bids_yesterday.append(prev['bid'])

    # --- Bidding Logic --- START

    # Critical HP: Bid very high to survive
    if my_status['hp'] <= 1: # If only 1 day left without water
        return min(my_status['budget'], DAILY_SALARY * 0.95 + 10)

    # If supply is very low, competition is fierce
    # If supply is just enough for me, I need to outbid everyone
    if day_context['supply'] < WATER_REQ * 2: # Less than enough for two agents to get their full requirement
        if my_status['hp'] <= 3: # If somewhat critical
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        
        # If strong opponents are present and bid high yesterday, react
        if strong_opponent_bids_yesterday:
            max_strong_bid = max(strong_opponent_bids_yesterday)
            if max_strong_bid >= DAILY_SALARY * 0.7: # If strong opps are bidding high
                return min(my_status['budget'], max_strong_bid + 5) # Slightly outbid them
            
        # Default for low supply, not critical HP
        return min(my_status['budget'], DAILY_SALARY * 0.75)


    # General strategy for normal supply scenarios
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If strong opponents were aggressive yesterday
        if strong_opponent_bids_yesterday and max(strong_opponent_bids_yesterday) >= DAILY_SALARY * 0.8:
            # If my HP is good, try to save
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.6)
            # If my HP is not great, be competitive
            return min(my_status['budget'], max(highest_prev_bid + 2, DAILY_SALARY * 0.85))

        # If overall highest bid was high (but not necessarily from strong opps, or strong opps were not highest)
        if highest_prev_bid >= DAILY_SALARY * 0.7:
            # If my HP is good, try to save a bit
            if my_status['hp'] > 4:
                return min(my_status['budget'], DAILY_SALARY * 0.5)
            # Otherwise, be competitive
            return min(my_status['budget'], highest_prev_bid + 1.5)
        
        # If yesterday's bids were generally moderate or low
        # Bid slightly above the average or a safe amount
        return min(my_status['budget'], max(DAILY_SALARY * 0.55, highest_prev_bid + 1))

    # Fallback if no previous bids (e.g., Day 1 or all opponents died yesterday)
    # Be moderately aggressive on Day 1 or if no history
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.8) # High bid if critical
    
    # If not critical, bid moderately
    return min(my_status['budget'], DAILY_SALARY * 0.6)
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    # Calculate potential HP loss if no water is acquired today
    # If no_water_days = 0, loss is 1. If 1, loss is 2. If 2, loss is 4. If 3, loss is 8.
    hp_loss_if_no_water = 2**(my_no_water_days) if my_no_water_days > 0 else 1

    # Desperation threshold: If my HP is at or below the potential loss for *next* day, bid aggressively.
    # Using a slightly higher threshold for safety.
    if my_hp <= hp_loss_if_no_water + 2: 
        return min(my_budget, DAILY_SALARY * 1.15) 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid
    base_bid = DAILY_SALARY * 0.7 # A reasonable default bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # React to opponent bidding patterns
        if highest_prev_bid > DAILY_SALARY * 0.9: # Opponents are bidding very high
            base_bid = max(base_bid, highest_prev_bid + 5)
        elif highest_prev_bid > DAILY_SALARY * 0.7: # Opponents are bidding moderately high
            base_bid = max(base_bid, highest_prev_bid + 2)
        elif highest_prev_bid < DAILY_SALARY * 0.5: # Opponents are bidding low
            # If there are many opponents, still need to outbid them reasonably
            if num_alive_opponents > 1:
                base_bid = max(base_bid, highest_prev_bid + 10)
            else: # Only one opponent, maybe can get it cheaper
                base_bid = max(base_bid, highest_prev_bid + 5)
                base_bid = min(base_bid, DAILY_SALARY * 0.7) # Don't overbid too much if they're weak
        else: # Moderate range
            base_bid = max(base_bid, highest_prev_bid + 1)

    # Adjust for remaining days (end game push)
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: 
        if my_budget > DAILY_SALARY * 1.5 and my_hp > 1: 
            base_bid = max(base_bid, DAILY_SALARY * 1.0) 
        elif my_hp <= 2: 
            base_bid = max(base_bid, DAILY_SALARY * 1.2) 

    # If I have very high budget and HP, and it's early in the game, try to conserve budget if opponents are weak
    if my_budget > DAILY_SALARY * 5 and my_hp > 8 and current_day < EPISODE_DAYS / 2:
        if yesterday_bids and max(yesterday_bids) < DAILY_SALARY * 0.6:
            base_bid = min(base_bid, DAILY_SALARY * 0.55)

    # Ensure the bid is not negative and does not exceed current budget
    final_bid = max(0.0, min(my_budget, base_bid))

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

    # If no opponents, bid conservatively to get water
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0

    # Base bid
    bid = DAILY_SALARY * 0.5 # 75

    # Adjust bid based on my HP and no_water_days
    if my_hp <= 2: # Critical HP: bid very high to survive
        bid = DAILY_SALARY * 0.95 # 142.5
    elif my_no_water_days > 0: # Missed water yesterday: bid aggressively
        bid = DAILY_SALARY * 0.9 # 135
    elif my_hp <= 4: # Low HP: bid aggressively
        bid = DAILY_SALARY * 0.8 # 120
    else: # Good HP: adjust based on opponent's previous bids
        if max_prev_bid > DAILY_SALARY * 0.7: # Opponents were aggressive
            bid = max(bid, max_prev_bid + 5) # Try to outbid their max
        elif max_prev_bid > DAILY_SALARY * 0.5: # Moderate competition
            bid = max(bid, DAILY_SALARY * 0.65) # 97.5
        else: # Low competition or unknown, conservative but secure
            bid = max(bid, DAILY_SALARY * 0.55) # 82.5

    # End game pressure (last few days)
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_hp < 5: # If close to end and HP is not great
        bid = max(bid, DAILY_SALARY * 0.9) # 135

    # Ensure bid does not exceed budget
    final_bid = min(my_budget, bid)

    # Ensure a minimal bid if budget allows, to stay in the game
    if final_bid < 10 and my_budget > 0: # If final bid is too low but budget exists
        final_bid = min(my_budget, 10)
    elif final_bid == 0 and my_budget > 0: # If final bid is 0 but budget exists
        final_bid = min(my_budget, 1)

    return final_bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From Current Meta-Round State: episode_days: 10

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid - a reasonable portion of daily salary
    base_bid = DAILY_SALARY * 0.65

    # Adjustment for my desperation (low HP or consecutive no-water days)
    if my_hp <= 2 or my_no_water_days >= 1:
        base_bid = DAILY_SALARY * 0.98 # Very aggressive, almost full salary
    elif my_hp <= 4:
        base_bid = DAILY_SALARY * 0.85 # Aggressive
    elif my_hp <= 6:
        base_bid = DAILY_SALARY * 0.75 # Moderate

    # Adjustment for supply scarcity
    # If supply is just enough for my requirement or slightly more, competition is high.
    # My requirement is 13 units.
    if current_supply < WATER_REQ * 1.3: # e.g., supply < 16.9 (e.g., 15, 16)
        base_bid *= 1.2 # Increase bid by 20%
    elif current_supply < WATER_REQ * 1.6: # e.g., supply < 20.8 (e.g., 17, 18, 19, 20)
        base_bid *= 1.1 # Increase bid by 10%

    # Adjustment based on opponents' previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        max_opponent_bid = max(yesterday_bids)
        # If max opponent bid was above a certain threshold, consider outbidding it.
        if max_opponent_bid > DAILY_SALARY * 0.4: # If opponents were bidding somewhat competitively
            # Try to outbid by a small margin, but not less than our current base_bid.
            base_bid = max(base_bid, max_opponent_bid + (DAILY_SALARY * 0.05)) # Add 5% of salary, e.g., 7.5

    # Adjustment for late game (survival becomes critical)
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        base_bid = DAILY_SALARY * 0.95 # Be very aggressive to survive
    elif current_day >= EPISODE_DAYS - 4: # Last 4 days
        base_bid = max(base_bid, DAILY_SALARY * 0.8) # Ensure a strong bid

    # Establish a minimum competitive bid based on my urgency
    minimum_competitive_bid = DAILY_SALARY * 0.4
    if my_hp <= 4 or my_no_water_days >= 1: # If desperate, ensure minimum is higher
        minimum_competitive_bid = DAILY_SALARY * 0.6
    
    # Ensure the bid is at least the minimum competitive bid, then cap by budget
    final_bid = max(base_bid, minimum_competitive_bid)
    final_bid = min(final_bid, my_budget)

    return final_bid
"""
