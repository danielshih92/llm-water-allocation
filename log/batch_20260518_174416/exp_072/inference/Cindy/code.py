# ============================================================
# Experiment: exp_072
# Agent: Cindy
# Source: exp_072
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
    num_alive_opponents = len(alive_opponents)
    
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_supply = day_context['supply']

    bid_multiplier = 0.0

    if num_alive_opponents == 0:
        bid_multiplier = 0.1 
    else:
        if my_hp <= 2: 
            bid_multiplier = 0.9
        elif my_hp == 3: 
            bid_multiplier = 0.7
        else: 
            bid_multiplier = 0.5 

        if current_supply <= 18: 
            bid_multiplier += 0.15
        elif current_supply <= 22: 
            bid_multiplier += 0.05

        bid_multiplier = min(bid_multiplier, 0.98)
        bid_multiplier = max(bid_multiplier, 0.1)

    final_bid = DAILY_SALARY * bid_multiplier
    
    return min(my_budget, final_bid)
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

    # If I'm the only one left, bid minimal to survive
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid
    # Start with a moderate bid, assuming some competition
    bid = DAILY_SALARY * 0.5 # 75

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        
        # Define a competitive threshold for bids. Bids below this are considered passive.
        competitive_threshold = DAILY_SALARY * 0.3 # 45

        if max_prev_bid >= competitive_threshold:
            # If the highest bid was competitive, we need to outbid it by a small margin
            bid = max(bid, max_prev_bid + 5.0)
        else:
            # If the highest bid was low (passive), we still ensure we bid above it,
            # but maintain a reasonable base if no strong competition is observed.
            bid = max(bid, max_prev_bid + 2.0)
    
    # Adjust based on my HP (survival priority)
    if my_status['hp'] <= 3: # Critical HP (1-3), must get water
        bid = max(bid, DAILY_SALARY * 0.9) # Bid very high (135)
    elif my_status['hp'] <= 5: # Low HP (4-5), prioritize water
        bid = max(bid, DAILY_SALARY * 0.75) # Bid high (112.5)

    # Adjust based on remaining days (end game aggression)
    current_day = day_context['day']
    days_remaining = EPISODE_DAYS - current_day
    
    # If it's the last couple of days and I'm still alive, be more aggressive.
    if days_remaining <= 2 and my_status['hp'] > 0:
        bid = max(bid, DAILY_SALARY * 0.8) # 120

    # Ensure bid does not exceed current budget
    bid = min(bid, my_status['budget'])

    # Ensure bid is at least a minimal amount, but only if budget allows it.
    # If budget is 0, bid should be 0.
    if my_status['budget'] > 0:
        bid = max(bid, 1.0)
    else:
        bid = 0.0 # If budget is 0, explicitly bid 0

    return bid
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

    bid_amount = DAILY_SALARY * 0.6 # Default moderate bid

    if not alive_opponents:
        bid_amount = DAILY_SALARY * 0.1 # Bid low to save money if no competition
        return max(0.0, min(my_status['budget'], bid_amount))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        HIGH_COMPETITION_THRESHOLD = DAILY_SALARY * 0.85 # 127.5

        if highest_prev_bid >= HIGH_COMPETITION_THRESHOLD:
            if my_status['hp'] > 5: # Relatively safe HP
                bid_amount = DAILY_SALARY * 0.4 # Risk a lower bid to save budget
            else: # Low HP, need water desperately
                bid_amount = DAILY_SALARY * 0.95 # Bid very high
        else:
            bid_amount = max(DAILY_SALARY * 0.5, highest_prev_bid + 5.0)
    else:
        if my_status['hp'] <= 3: # Low HP, need water
            bid_amount = DAILY_SALARY * 0.9
        else: # Normal HP
            bid_amount = DAILY_SALARY * 0.6

    day_factor = 1 + (day_context['day'] / EPISODE_DAYS) * 0.15
    bid_amount *= day_factor

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    # Base bid calculation based on my daily salary and current health
    base_bid = DAILY_SALARY * 0.75 # Start with a moderate bid

    # Adjust aggressively if HP is critical or water was missed recently
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        base_bid = DAILY_SALARY * 0.98 # Bid very aggressively to survive
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.90 # Bid aggressively
    
    # Adjust based on supply scarcity (supply affects competition)
    supply = day_context['supply']
    supply_factor = 1.0
    if supply <= MIN_SUPPLY + 2: # Very low supply, high competition
        supply_factor = 1.15
    elif supply <= MIN_SUPPLY + 5: # Low supply
        supply_factor = 1.05
    elif supply >= MAX_SUPPLY - 3: # High supply, less competition
        supply_factor = 0.90
    elif supply >= MAX_SUPPLY - 5: # Slightly high supply
        supply_factor = 0.95
    base_bid *= supply_factor

    # Opponent analysis from previous_trace to react to their last bid
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents bid very high (e.g., > 90% of our daily salary)
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            if my_status['hp'] > 3: # If healthy, try to conserve or slightly undercut
                # If supply is still scarce, we might need to compete more
                if supply <= MIN_SUPPLY + 3:
                    base_bid = max(base_bid, highest_prev_bid * 1.01) # Slightly outbid
                else:
                    base_bid = min(base_bid, DAILY_SALARY * 0.7) # Conserve if not critical
            else: # Not healthy, must compete aggressively
                base_bid = max(base_bid, highest_prev_bid + 2.0) # Ensure outbid
        # If opponents bid moderately high (e.g., > 60% of our daily salary)
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            base_bid = max(base_bid, highest_prev_bid + 1.0) # Match or slightly exceed
        # If opponents bid low
        else:
            if my_status['hp'] > 3: # Healthy, try to get it very cheap
                base_bid = min(base_bid, highest_prev_bid + 1.0) # Bid just above them
            else: # Not healthy, ensure we get water, but don't overpay if they bid low
                base_bid = max(base_bid, DAILY_SALARY * 0.65) # Ensure a safe, competitive bid

    # Ensure final bid does not exceed current budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure bid is non-negative. If budget is positive but final_bid is 0, and I need water,
    # make a minimal bid to stay in the game.
    if final_bid <= 0.0 and my_status['budget'] > 0.0 and my_status['hp'] <= 4:
        final_bid = min(my_status['budget'], 1.0) # Bid 1 to try and get something

    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimum to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Identify strong opponents from previous meta-round context
    strong_opponents_ids = ["Eric", "Alex"]
    
    strong_opponents_alive_bids = []
    other_opponents_alive_bids = []

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            if opp['agent_id'] in strong_opponents_ids:
                strong_opponents_alive_bids.append(prev['bid'])
            else:
                other_opponents_alive_bids.append(prev['bid'])

    # Determine base bid
    base_bid = DAILY_SALARY * 0.5 # Default moderate bid
    
    highest_prev_bid = 0.0
    if strong_opponents_alive_bids:
        highest_prev_bid = max(strong_opponents_alive_bids)
    elif other_opponents_alive_bids: # If no strong opponents, consider others
        highest_prev_bid = max(other_opponents_alive_bids)
    
    # If there was a previous bid, adjust base_bid to outbid slightly
    if highest_prev_bid > 0:
        base_bid = max(base_bid, highest_prev_bid + 1.0)

    # Aggressive bidding if HP is low or no water days are high
    if my_status['hp'] <= 3 or my_status['no_water_days'] > 0:
        base_bid = max(base_bid, DAILY_SALARY * 0.9) # Be very aggressive
        # If very critical, bid even higher, potentially exceeding salary
        if my_status['hp'] <= 1 or my_status['no_water_days'] >= 1:
            base_bid = max(base_bid, DAILY_SALARY * 1.1)
            # If supply is low, competition is higher, bid even more aggressively
            # Check if supply is less than water required for all alive opponents
            if day_context['supply'] <= WATER_REQ * len(alive_opponents):
                 base_bid = max(base_bid, DAILY_SALARY * 1.25)

    # Also consider late game pressure
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: # Last 2 days, bid aggressively to survive
        base_bid = max(base_bid, DAILY_SALARY * 1.0)
        if my_status['hp'] <= 3: # Very critical late game
            base_bid = max(base_bid, DAILY_SALARY * 1.3)

    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], base_bid)
    
    # Ensure bid is at least a small amount to participate
    final_bid = max(final_bid, 1.0)

    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    calculated_bid = DAILY_SALARY * 0.55 # Default bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # React to very high previous bids (e.g., Eric's typical max bids)
        if highest_prev_bid >= DAILY_SALARY * 0.85: # 127.5 for Cindy
            if my_status['hp'] > 3:
                # If HP is good, be competitive but try to save slightly
                calculated_bid = max(DAILY_SALARY * 0.6, highest_prev_bid + 1.0)
            else:
                # If HP is low, bid very high to secure water
                calculated_bid = DAILY_SALARY * 0.95 # 142.5
        
        # React to moderately high previous bids (e.g., Bob/David's typical bids)
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # 75.0 for Cindy
            if my_status['hp'] <= 3:
                # Low HP, be aggressive
                calculated_bid = DAILY_SALARY * 0.9 # 135.0
            else:
                # HP is okay, try to outbid slightly or maintain competitive pressure
                calculated_bid = max(DAILY_SALARY * 0.65, highest_prev_bid + 2.5)
        
        # React to low previous bids
        else:
            if my_status['hp'] <= 3:
                # Low HP, still need water, but can be less aggressive
                calculated_bid = DAILY_SALARY * 0.8 # 120.0
            else:
                # HP is good, try to save budget
                calculated_bid = DAILY_SALARY * 0.45 # 67.5
    
    # Independent HP/no_water_days based adjustment (can override previous calculated_bid if more critical)
    if my_status['no_water_days'] > 0:
        calculated_bid = DAILY_SALARY * 0.99 # Critical situation, bid almost full salary
    elif my_status['hp'] <= 2:
        calculated_bid = max(calculated_bid, DAILY_SALARY * 0.9) # 135.0
    elif my_status['hp'] <= 4:
        calculated_bid = max(calculated_bid, DAILY_SALARY * 0.75) # 112.5

    # Ensure bid does not exceed budget and is always positive
    final_bid = min(my_status['budget'], calculated_bid)
    final_bid = max(final_bid, 1.0) # Minimum bid of 1.0
    
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

    # If no opponents, bid minimum to get water and save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Get yesterday's bids for all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_prev_bid = 0
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)

    # Determine base bid strategy
    # Default bid: moderately aggressive
    base_bid = DAILY_SALARY * 0.8 # 120

    # Adjust based on my HP and no_water_days
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        # Critical state, must get water. Bid very aggressively.
        base_bid = DAILY_SALARY * 0.95 # 142.5
        if day_context['day'] >= EPISODE_DAYS - 2: # Last couple of days, go all in if critical
            base_bid = DAILY_SALARY + 5 # 155
    elif my_status['hp'] >= 8 and len(alive_opponents) > 0:
        # Healthy, can afford to be less aggressive if competition is high
        if max_prev_bid > DAILY_SALARY * 0.9: # If opponents bid very high (over 135)
            base_bid = DAILY_SALARY * 0.7 # Try to save money (105)
        else:
            base_bid = DAILY_SALARY * 0.75 # (112.5)

    # If there's a strong previous bid, try to beat it
    if max_prev_bid > 0 and base_bid <= max_prev_bid:
        base_bid = max_prev_bid + 1.0

    # Consider opponents' budgets. If all remaining opponents have very low budget, no need to overbid.
    low_budget_opponents = [o for o in alive_opponents if o['budget'] < DAILY_SALARY * 0.5]

    if len(low_budget_opponents) == len(alive_opponents) and len(alive_opponents) > 0:
        # All remaining opponents seem to have low budget
        if max_prev_bid > 0:
            base_bid = min(base_bid, max_prev_bid + 1.0, DAILY_SALARY * 0.6) # Cap at 90
        else:
            base_bid = min(base_bid, DAILY_SALARY * 0.4) # Cap at 60

    # Ensure bid does not exceed my budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure bid is at least 1 to participate
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid, scaled by my salary
    base_bid = DAILY_SALARY * 0.55

    # Adjust based on my HP
    if my_hp <= 2: # Critical HP
        base_bid = DAILY_SALARY * 1.5 # Bid very aggressively, potentially more than salary
    elif my_hp <= 5: # Low HP
        base_bid = DAILY_SALARY * 1.0
    elif my_no_water_days > 0: # Missed water yesterday
        base_bid = DAILY_SALARY * 1.2

    # Adjust based on supply scarcity
    if num_alive_opponents > 0:
        total_water_needed = (num_alive_opponents + 1) * WATER_REQ
        if current_supply < total_water_needed: # Supply is tight
            num_can_get_water = int(current_supply // WATER_REQ)
            if num_can_get_water < (num_alive_opponents + 1): # Not everyone can get their full water
                scarcity_multiplier = 1.0 + (1.0 - (current_supply / total_water_needed)) * 0.5 # Up to 50% increase for extreme scarcity
                base_bid *= scarcity_multiplier
                # If my HP is good, don't overpay too much due to scarcity
                if my_hp > 5:
                    base_bid = min(base_bid, DAILY_SALARY * 1.2) # Cap scarcity-driven bid if healthy

    # React to yesterday's opponent bids
    yesterday_winning_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and prev.get('status') == 'won':
            opp_salary = opp['daily_salary']
            if opp_salary > 0:
                scaled_opp_bid = (prev['bid'] / opp_salary) * DAILY_SALARY
                yesterday_winning_bids.append(scaled_opp_bid)
            else: # Handle case where opponent salary is 0 to avoid division by zero
                yesterday_winning_bids.append(prev['bid']) # Use raw bid if salary is 0 (unlikely but safe)

    if yesterday_winning_bids:
        max_prev_winning_bid = max(yesterday_winning_bids)
        avg_prev_winning_bid = sum(yesterday_winning_bids) / len(yesterday_winning_bids)

        # If opponents bid very high yesterday (relative to their salary, scaled to mine)
        if max_prev_winning_bid >= DAILY_SALARY * 1.2: # Very high pressure
            if my_hp > 5: # If I'm relatively healthy, I can try to save a bit, but still need to compete
                base_bid = max(base_bid, max_prev_winning_bid * 0.9) # Try to win but not overpay too much
            else: # Critical HP, must win
                base_bid = max(base_bid, max_prev_winning_bid + (DAILY_SALARY * 0.1)) # Bid slightly above to secure
        elif max_prev_winning_bid >= DAILY_SALARY * 0.8: # Moderate pressure
            base_bid = max(base_bid, avg_prev_winning_bid * 1.05) # Bid slightly above average to secure

    # Late game aggressiveness (last few days)
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2:
        if my_hp > 0: # If I'm still alive, try to finish strong
            base_bid = max(base_bid, DAILY_SALARY * 1.3) # Ensure survival, bid aggressively
        else: # If I'm already dead or dying, don't waste budget
            base_bid = 0.0

    # Ensure bid is not negative and within budget
    final_bid = min(my_budget, max(0.0, base_bid))

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
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If I'm the only one left, bid minimal
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Analyze opponent bids from yesterday's trace, focusing on strong competitors
    max_prev_bid_strong_opponents = 0.0
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev_trace = opp_data.get('previous_trace', {})
            prev_bid = prev_trace.get('bid', 0.0)

            # Eric was the top performer, Alex was also competitive
            if opp_id in ["Eric", "Alex"]:
                max_prev_bid_strong_opponents = max(max_prev_bid_strong_opponents, prev_bid)

    # Determine bidding pressure based on supply and competitors
    # Given supply_range [15, 25] and WATER_REQ 13, it means:
    # - current_supply is always >= WATER_REQ (13)
    # - current_supply is always < (2 * WATER_REQ) (26)
    # So, competition is always high as only one agent can get full water.

    bid = 0.0

    # Critical health: Must get water
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        # Bid aggressively, considering strong opponents' previous bids
        desperation_bid = max(DAILY_SALARY * 1.2, max_prev_bid_strong_opponents * 1.05)
        if my_status['hp'] <= 1: # Even more desperate
            desperation_bid = max(DAILY_SALARY * 1.5, max_prev_bid_strong_opponents * 1.1)
        
        bid = desperation_bid

        # If it's the last few days, bid very high to survive
        if current_day >= EPISODE_DAYS - 2:
            bid = max(bid, DAILY_SALARY * 2.0) 
        
        # Ensure a minimum competitive bid when desperate
        bid = max(bid, DAILY_SALARY * 0.8)

    # Healthy state: Compete to win the single water slot
    else:
        # If strong opponents are alive, bid just above their previous high
        if max_prev_bid_strong_opponents > 0:
            bid = max(DAILY_SALARY * 0.95, max_prev_bid_strong_opponents + 5.0)
        else: # No strong previous bids, but supply is tight
            bid = DAILY_SALARY * 1.0
        
        # If it's late in the game, increase bid to secure water
        if current_day >= EPISODE_DAYS - 3:
            bid = max(bid, DAILY_SALARY * 1.1)

    # Ensure bid is always positive and does not exceed budget.
    bid = max(0.1, bid) # Minimum bid to participate
    bid = min(bid, my_status['budget'])

    # Cap bid at a reasonable maximum to prevent overspending, unless it's the very last day
    max_reasonable_bid = DAILY_SALARY * 1.8
    if current_day == EPISODE_DAYS: # Last day, bid everything if needed
        max_reasonable_bid = my_status['budget']
    
    bid = min(bid, max_reasonable_bid)

    return bid
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
    
    # If no opponents are alive, bid low to save money
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Emergency bidding if HP is critically low, takes highest precedence
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    # Collect yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Determine aggressive bidding threshold based on typical high bids (e.g., Eric's behavior)
    HIGH_BID_THRESHOLD = DAILY_SALARY * 0.85

    # Strategy based on highest previous bid
    if highest_prev_bid >= HIGH_BID_THRESHOLD:
        # High competition detected. Eric or another strong opponent is likely bidding aggressively.
        # Bid aggressively to compete, but manage budget if possible.
        if my_status['hp'] <= 4: # HP is getting low, need water more
            # Try to outbid the highest previous bid, with a strong floor
            return min(my_status['budget'], max(DAILY_SALARY * 0.8, highest_prev_bid + 2.0))
        else: # HP is relatively healthy, can afford to be slightly less aggressive or match
            # Try to outbid slightly, with a moderate floor
            return min(my_status['budget'], max(DAILY_SALARY * 0.7, highest_prev_bid + 1.0))
    else:
        # Moderate or low competition detected.
        # Bid moderately, slightly above previous if any, or a default value.
        if my_status['hp'] <= 5: # HP is somewhat low, be a bit more aggressive than default
            return min(my_status['budget'], max(DAILY_SALARY * 0.65, highest_prev_bid + 1.0))
        else: # HP is healthy, bid a standard moderate amount
            return min(my_status['budget'], max(DAILY_SALARY * 0.55, highest_prev_bid + 0.5))
"""
