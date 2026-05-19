# ============================================================
# Experiment: exp_011
# Agent: Cindy
# Source: exp_011
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
    EPISODE_DAYS = 10

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_supply = day_context['supply']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid strategy
    base_bid = DAILY_SALARY * 0.7

    # Adjust bid based on my HP
    if my_hp <= 2: # Critical HP, need water desperately
        base_bid = DAILY_SALARY * 1.1
    elif my_hp <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.9
    elif my_hp >= 7: # High HP, can afford to be more conservative
        base_bid = DAILY_SALARY * 0.55

    # Adjust bid based on supply scarcity
    if current_supply <= MIN_SUPPLY + WATER_REQ - 1: # Very low supply, high competition
        base_bid *= 1.15
    elif current_supply <= (MIN_SUPPLY + MAX_SUPPLY) / 2: # Medium-low supply
        base_bid *= 1.05
    elif current_supply >= MAX_SUPPLY - WATER_REQ + 1: # High supply, can be less aggressive
        base_bid *= 0.9

    # Adjust bid based on number of active opponents
    if num_alive_opponents >= 2: # More competition
        base_bid *= 1.1
    elif num_alive_opponents == 1: # Head-to-head
        base_bid *= 1.05
    else: # No opponents, bid minimum to get water
        return min(my_budget, 1)

    # Look at yesterday's bids from opponents if available (exploitation of previous_trace)
    highest_prev_opp_bid = 0
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            highest_prev_opp_bid = max(highest_prev_opp_bid, prev_trace['bid'])

    if highest_prev_opp_bid > 0:
        # If opponents bid high yesterday, react by trying to outbid them
        if highest_prev_opp_bid >= DAILY_SALARY * 0.9: 
            base_bid = max(base_bid, highest_prev_opp_bid + 5)
        else:
            base_bid = max(base_bid, highest_prev_opp_bid + 1)

    # Special case: End of game, if I have a lot of budget, secure water
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_hp <= 3: # Near end and low HP
        base_bid = max(base_bid, DAILY_SALARY * 1.2)

    # Final bid must be within budget and non-negative
    final_bid = min(my_budget, max(1, base_bid))
    
    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    # Identify strong competitors based on meta-round context (Alex, Bob)
    # and filter for those currently alive.
    strong_competitor_ids = ["Alex", "Bob"]
    
    alive_strong_competitors_prev_bids = []
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive'] and opp_id in strong_competitor_ids:
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None and prev_trace.get('error') is None:
                alive_strong_competitors_prev_bids.append(prev_trace['bid'])

    # Determine the highest bid from strong competitors yesterday
    max_prev_bid_strong_competitors = 0.0
    if alive_strong_competitors_prev_bids:
        max_prev_bid_strong_competitors = max(alive_strong_competitors_prev_bids)

    # Determine a base bid based on my current HP
    # If HP is low, bid more aggressively.
    my_current_hp = my_status['hp']
    
    if my_current_hp <= 2: # Critical health
        base_bid = DAILY_SALARY * 0.95
    elif my_current_hp <= 4: # Low health
        base_bid = DAILY_SALARY * 0.8
    else: # Healthy
        base_bid = DAILY_SALARY * 0.6

    # Adjust my bid based on competitors' previous bids
    # Try to slightly outbid strong competitors, but not less than my base_bid
    my_bid = max(base_bid, max_prev_bid_strong_competitors + 1.0)

    # Ensure bid does not exceed available budget
    my_bid = min(my_status['budget'], my_bid)

    # Ensure a minimum bid to participate
    my_bid = max(my_bid, 1.0)
    
    return my_bid
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid = DAILY_SALARY * 0.55

    remaining_days = EPISODE_DAYS - current_day
    if my_status['hp'] <= 2 or remaining_days <= 2:
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        bid = DAILY_SALARY * 0.75

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 3 and remaining_days > 2:
                bid = max(bid, highest_prev_bid * 0.98)
            else:
                bid = max(bid, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            bid = max(bid, highest_prev_bid + 2)
        else:
            bid = max(bid, highest_prev_bid + 1)
            
    num_potential_winners = int(current_supply // WATER_REQ)
    num_competitors = len(alive_opponents) + 1

    if num_competitors > num_potential_winners and num_potential_winners > 0:
        if my_status['hp'] <= 3:
            bid = max(bid, DAILY_SALARY * 0.98)
        else:
            bid = max(bid, DAILY_SALARY * 0.8)

    final_bid = min(my_status['budget'], bid)
    final_bid = max(1.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)
    
    # Base bid: a fraction of daily salary
    base_bid = DAILY_SALARY * 0.7 
    
    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Very low HP, highly desperate
        base_bid = DAILY_SALARY * 1.2
    elif my_status['hp'] <= 4: # Low HP, desperate
        base_bid = DAILY_SALARY * 1.0
    elif my_status['hp'] >= 8: # High HP, can afford to be more conservative
        base_bid = DAILY_SALARY * 0.6
        
    # Analyze competition from yesterday's bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
    # Adjust bid based on supply vs. demand and opponent behavior
    current_supply = day_context['supply']
    
    # Number of water "slots" available for my water requirement (always 1 for Cindy with WATER_REQ=13 and supply 15-25)
    num_my_slots = int(current_supply // WATER_REQ) 
    
    # If supply is very tight (e.g., only one slot for me or fewer slots than competitors)
    if num_my_slots < num_alive_opponents + 1: # High competition scenario (true if any opponents are alive)
        if my_status['hp'] <= 4: # If desperate, bid to win
            base_bid = max(base_bid, highest_prev_bid * 1.05 + 5 if highest_prev_bid > 0 else DAILY_SALARY * 1.1)
        else: # Less desperate, but still competitive
            base_bid = max(base_bid, highest_prev_bid * 1.02 + 1 if highest_prev_bid > 0 else DAILY_SALARY * 0.9)
    else: # Enough supply for everyone (only if no opponents are alive)
        if my_status['hp'] <= 2: # Still desperate if low HP, even with good supply
            base_bid = max(base_bid, highest_prev_bid * 1.03 + 2 if highest_prev_bid > 0 else DAILY_SALARY * 1.0)
        else: # Can be more conservative
            base_bid = min(base_bid, highest_prev_bid * 0.95 if highest_prev_bid > 0 else DAILY_SALARY * 0.5)

    # Ensure bid is at least a minimum to stay in the game, but not more than budget
    min_bid_to_stay_alive = DAILY_SALARY * 0.1
    final_bid = max(min_bid_to_stay_alive, base_bid)
    
    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], final_bid)
    
    # If budget is very low, bid almost all remaining budget to survive if desperate
    if my_status['budget'] < DAILY_SALARY * 0.5 and my_status['hp'] <= 3:
        final_bid = my_status['budget'] * 0.95 
        
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

    # If no opponents are alive, bid a minimal amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid_value = 0.0 # Initialize bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # Scenario 1: Yesterday's highest bid was very high (competitive)
        if highest_prev_bid >= DAILY_SALARY * 0.85: # 150 * 0.85 = 127.5
            if my_status['hp'] > 3: # If my HP is good, try to conserve budget
                bid_value = DAILY_SALARY * 0.3 # 150 * 0.3 = 45
            else: # If my HP is critical, bid very high to survive
                bid_value = DAILY_SALARY * 0.95 # 150 * 0.95 = 142.5
        # Scenario 2: Yesterday's highest bid was not extremely high
        else:
            # Bid slightly above yesterday's highest, but at least a moderate amount
            bid_value = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5) # 150 * 0.5 = 75
    else:
        # If no previous bids are available (e.g., Day 1 of a meta-round or opponents died)
        # Apply a default strategy based on my HP
        if my_status['hp'] <= 2: # Critical HP, bid high
            bid_value = DAILY_SALARY * 0.9 # 150 * 0.9 = 135
        else: # Normal HP, bid moderately
            bid_value = DAILY_SALARY * 0.55 # 150 * 0.55 = 82.5

    # Ensure the bid does not exceed my current budget
    bid_value = min(my_status['budget'], bid_value)
    
    # Ensure the bid is at least 1.0 if I have budget, otherwise 0.0
    if my_status['budget'] > 0:
        bid_value = max(bid_value, 1.0)
    else:
        bid_value = 0.0

    return bid_value
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    # Base bid: A competitive bid based on observed opponent averages from meta-round context
    base_bid = DAILY_SALARY * 0.65 # 97.5

    # Determine if I'm desperate for water
    is_desperate = my_status['hp'] <= 2 or my_status['no_water_days'] > 0
    
    # Calculate initial bid
    current_bid = base_bid

    # Consider opponent bids from yesterday
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents bid very high yesterday (e.g., > 80% of daily salary)
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if is_desperate:
                current_bid = DAILY_SALARY * 0.95 # Bid very high to survive
            else:
                # If not desperate, but competition is high, still need to be competitive
                current_bid = max(base_bid, highest_prev_bid + 2) # Try to slightly outbid them
        else:
            # Opponents were not extremely aggressive, try to slightly outbid or maintain base
            current_bid = max(base_bid, highest_prev_bid + 1)
    
    # If no previous bids from opponents, or it's day 1, use base bid. Override if desperate.
    if is_desperate:
        current_bid = max(current_bid, DAILY_SALARY * 0.9) # Ensure high bid if desperate

    # Late game pressure: Increase bid significantly in the final days
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days
        current_bid = max(current_bid, DAILY_SALARY * 0.95) # Be very aggressive

    # If no opponents are alive, bid minimally to save budget
    if not alive_opponents:
        current_bid = DAILY_SALARY * 0.1 # Minimal bid

    # Ensure bid doesn't exceed budget
    final_bid = min(current_bid, my_status['budget'])

    # Ensure bid is at least 1 to participate
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    # Base bid: Start competitive, considering opponents' past high bids
    target_bid = DAILY_SALARY * 0.9 # Initial competitive bid of 135

    # Adjustment based on my health and water deprivation
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        # Critical state: bid aggressively to survive
        target_bid = DAILY_SALARY * 1.1 # 165
    elif my_status['hp'] >= 8 and my_status['no_water_days'] == 0:
        # Healthy state: conserve budget
        target_bid = DAILY_SALARY * 0.7 # 105

    # Adjustment based on opponent's previous day bids
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            # Opponents are bidding high, be ready to outbid them
            target_bid = max(target_bid, highest_prev_bid + 5)
        elif highest_prev_bid < DAILY_SALARY * 0.6:
            # Opponents are bidding low, try to get water cheaper
            target_bid = min(target_bid, highest_prev_bid + 1)

    # Adjustment based on supply scarcity
    supply_level = day_context['supply']
    if supply_level <= MIN_SUPPLY + 2: # Very low supply (e.g., 15, 16, 17)
        target_bid *= 1.15
    elif supply_level >= MAX_SUPPLY - 2: # Very high supply (e.g., 23, 24, 25)
        target_bid *= 0.85

    # Ensure bid does not exceed budget and is at least a minimum value
    final_bid = min(my_status['budget'], target_bid)
    final_bid = max(0.1, final_bid) # Minimum bid to participate

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
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid_amount = DAILY_SALARY * 0.6

    # Survival logic: Prioritize water if HP is low
    if my_status['hp'] <= 2:
        bid_amount = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        bid_amount = DAILY_SALARY * 0.8

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents bid high, be aggressive
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] <= 6:
                bid_amount = max(bid_amount, highest_prev_bid + 5.0)
            else:
                bid_amount = max(bid_amount, highest_prev_bid * 0.98)
        # If opponents bid low, try to win cheaply
        elif highest_prev_bid < DAILY_SALARY * 0.5:
            if my_status['hp'] > 4:
                bid_amount = min(bid_amount, highest_prev_bid + 10.0)
            else:
                bid_amount = max(bid_amount, highest_prev_bid + 20.0)
        else: # Moderate previous bids
            bid_amount = max(bid_amount, highest_prev_bid + 2.0)

    # End game adjustment: Increase aggression if nearing the end and HP isn't full
    if day_context['day'] >= EPISODE_DAYS - 3 and my_status['hp'] < EPISODE_DAYS:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.85)

    final_bid = min(my_status['budget'], bid_amount)
    
    if final_bid <= 0 and my_status['budget'] > 0:
        return 1.0
    
    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid conservatively to maximize budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid
    bid_value = DAILY_SALARY * 0.55 # Default moderate bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        num_slots = int(day_context['supply'] / WATER_REQ)
        num_alive_players = len(alive_opponents) + 1 # Including myself

        # Scenario 1: High competition (not enough water for everyone)
        if num_slots < num_alive_players:
            if my_status['hp'] <= 2: # Critical HP
                bid_value = DAILY_SALARY * 0.95
            elif my_status['hp'] <= 4: # Low HP
                bid_value = max(DAILY_SALARY * 0.7, highest_prev_bid + 5)
            else: # Healthy HP but high competition
                bid_value = max(DAILY_SALARY * 0.6, highest_prev_bid + 2)
        # Scenario 2: Low competition (enough water for everyone)
        else:
            if highest_prev_bid >= DAILY_SALARY * 0.85: # Opponents bid very high yesterday
                if my_status['hp'] > 3: # My HP is good, try to save
                    bid_value = DAILY_SALARY * 0.3
                else: # My HP is not good, secure water
                    bid_value = DAILY_SALARY * 0.9
            else: # Opponents bid moderately yesterday
                if my_status['hp'] <= 3: # My HP is low, bid a bit higher
                    bid_value = max(DAILY_SALARY * 0.6, highest_prev_bid + 1)
                else: # My HP is good, bid moderately
                    bid_value = max(DAILY_SALARY * 0.4, highest_prev_bid * 0.9)
    else: # No yesterday bids (e.g., Day 1, or all opponents had errors)
        if my_status['hp'] <= 2: # Critical HP
            bid_value = DAILY_SALARY * 0.9
        else: # Healthy HP
            bid_value = DAILY_SALARY * 0.55 # Default moderate bid

    # Ensure bid does not exceed budget and is at least 1.0
    final_bid = min(my_status['budget'], bid_value)
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid low to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid strategy
    my_current_bid = DAILY_SALARY * 0.6 # Moderate base bid

    # Priority 1: Critical health or no water days
    if my_status['no_water_days'] > 0:
        my_current_bid = DAILY_SALARY * 0.95 # Bid very high to ensure water
    elif my_status['hp'] <= 2:
        my_current_bid = DAILY_SALARY * 0.9 # Bid high

    # Priority 2: Low health
    elif my_status['hp'] <= 4:
        my_current_bid = DAILY_SALARY * 0.75 # Bid moderately high

    # Adjust bid based on yesterday's highest opponent bid if not in critical/low health
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if my_status['hp'] > 4 and my_status['no_water_days'] == 0: # Not desperate
            if highest_prev_bid >= DAILY_SALARY * 0.85: # Opponents were very aggressive
                # Try to save budget if not desperate, but still acknowledge high competition
                my_current_bid = min(my_current_bid, highest_prev_bid * 0.8) # Bid slightly lower than their peak, but not too low
            else:
                # Opponents were less aggressive, bid slightly above them to secure water
                my_current_bid = max(my_current_bid, highest_prev_bid + 2.0)
        else: # Desperate or low health, need to outbid
            my_current_bid = max(my_current_bid, highest_prev_bid + 5.0) # Ensure to outbid if possible

    # Consider supply scarcity
    if day_context['supply'] < WATER_REQ: # Not enough water for even one person
        if my_status['hp'] > 2: # Not critical, save budget
            return min(my_status['budget'], DAILY_SALARY * 0.1)
        else: # Critical, still try just in case, but don't overspend too much
            return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Ensure bid doesn't exceed budget
    final_bid = min(my_status['budget'], my_current_bid)

    # Ensure bid is at least 1.0 if budget allows, to participate
    return max(1.0, final_bid) if my_status['budget'] > 0 else 0.0
"""
