# ============================================================
# Experiment: exp_000
# Agent: Cindy
# Source: exp_000
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
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid just enough to get water or save money
    if not alive_opponents:
        if my_hp < 5: # If not full HP, try to get water
            return min(my_budget, DAILY_SALARY * 0.3)
        return min(my_budget, DAILY_SALARY * 0.1) # Conserve if full HP

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid strategy based on my health
    base_bid = DAILY_SALARY * 0.55 # Default moderate bid

    if my_hp <= 2 or my_no_water_days >= 1: # Very desperate
        base_bid = DAILY_SALARY * 0.95
    elif my_hp == 3: # Getting low
        base_bid = DAILY_SALARY * 0.75
    elif my_hp == 4: # Healthy but not full
        base_bid = DAILY_SALARY * 0.5

    # Adjust for supply scarcity/abundance
    num_competitors = len(alive_opponents) + 1
    total_potential_demand = num_competitors * WATER_REQ

    if current_supply < total_potential_demand: # Scarcity
        base_bid *= 1.1 # Increase bid
    elif current_supply >= total_potential_demand + WATER_REQ: # Abundance
        base_bid *= 0.9 # Decrease bid

    # Incorporate opponent's previous bids (exploitation of previous_trace)
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were very aggressive yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_hp > 3: # I'm relatively healthy, can afford to let them exhaust
                bid = min(base_bid, DAILY_SALARY * 0.3) # Try to conserve
            else: # I'm not healthy, must compete aggressively
                bid = max(base_bid, highest_prev_bid + 5) # Ensure I outbid
        else: # Opponents were not extremely aggressive
            bid = max(base_bid, highest_prev_bid + 2) # Slightly outbid to win
    else:
        # No previous bids (e.g., Day 1 or all opponents are new/had errors)
        bid = base_bid

    # End-game pressure
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and (my_hp <= 3 or my_no_water_days >= 1): # Near end and low HP or missed water
        bid = max(bid, DAILY_SALARY * 0.95) # Max aggression to survive last days

    # Ensure bid is within budget and non-negative
    final_bid = min(my_budget, max(0.0, bid))

    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid just enough to get water cheaply.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Initialize bid with a default value for a healthy state
    bid = DAILY_SALARY * 0.55 

    # Adjust bid based on my HP (priority)
    if my_status['hp'] <= 2: # Critical HP, must win
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP, need water
        bid = DAILY_SALARY * 0.75

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Further adjust bid based on opponent's previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # React to high bids from opponents (especially Eric)
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents bid very high
            if my_status['hp'] > 4: # Healthy, try to win but don't overspend too much
                bid = max(bid, highest_prev_bid + 5)
            else: # Not healthy, must win
                bid = max(bid, highest_prev_bid + 10) # Aggressively bid higher
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # Opponents bid moderately high
            bid = max(bid, highest_prev_bid + 2) # Slightly exceed to win
        else: # Opponents bid low
            bid = min(bid, highest_prev_bid + 1) # Try to win cheaply, but ensure it's at least 1 above

    # Adjust bid based on supply (fine-tuning)
    supply = day_context['supply']
    if supply < 18: # Low supply, increase bid slightly
        bid += DAILY_SALARY * 0.05
    elif supply > 22: # High supply, decrease bid slightly
        bid -= DAILY_SALARY * 0.05

    # Ensure bid is not negative and within budget
    final_bid = max(0.0, min(my_status['budget'], bid))

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    current_day = day_context['day']
    supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], 1.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    max_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    adjusted_supply_factor = 1 - supply_factor
    supply_adjustment = (DAILY_SALARY * 0.1) * adjusted_supply_factor
    
    calculated_bid = 0.0

    if not yesterday_bids or max_yesterday_bid < DAILY_SALARY * 0.4:
        calculated_bid = DAILY_SALARY * 0.55 + supply_adjustment
        if num_alive_opponents == 1 and max_yesterday_bid < DAILY_SALARY * 0.3:
            calculated_bid = max(max_yesterday_bid + 1, DAILY_SALARY * 0.2)
    else:
        if my_status['hp'] <= 3:
            calculated_bid = max(max_yesterday_bid + 5, DAILY_SALARY * 0.85)
        elif my_status['hp'] <= 6:
            calculated_bid = max(max_yesterday_bid + 3, DAILY_SALARY * 0.75)
        else:
            calculated_bid = max(max_yesterday_bid + 1, DAILY_SALARY * 0.65)

    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2:
        if my_status['hp'] <= 5:
            calculated_bid = max(calculated_bid, DAILY_SALARY * 0.9)
        elif my_status['hp'] <= 8:
            calculated_bid = max(calculated_bid, DAILY_SALARY * 0.8)
            
    final_bid = min(my_status['budget'], calculated_bid)
    
    if final_bid < 1.0 and my_status['budget'] >= 1.0:
        final_bid = 1.0
    elif my_status['budget'] == 0:
        final_bid = 0.0

    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to survive
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Collect previous bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Calculate total water required by all alive agents including myself
    total_water_required_by_all = WATER_REQ
    for opp in alive_opponents:
        total_water_required_by_all += opp['water_requirement']

    supply = day_context['supply']

    # Determine base bid strategy
    base_bid = DAILY_SALARY * 0.6 # A moderate starting bid

    # Adjust based on my HP
    if my_status['hp'] <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5: # Low HP
        base_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] >= 8 and my_status['budget'] > DAILY_SALARY * 2: # Healthy and good budget
        base_bid = DAILY_SALARY * 0.5

    # Adjust based on supply scarcity
    if supply < total_water_required_by_all:
        # Scarcity: bid higher to compete
        scarcity_factor = (total_water_required_by_all - supply) / total_water_required_by_all
        base_bid += DAILY_SALARY * scarcity_factor * 0.2 
    elif supply >= total_water_required_by_all + WATER_REQ: # Abundant supply
        # Abundant supply: bid lower to save budget
        base_bid = max(DAILY_SALARY * 0.4, base_bid * 0.8)

    # Adjust based on opponent previous bids (aggressive response)
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest bid was very high, it indicates strong competition
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, highest_prev_bid + 5) # Try to outbid
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            base_bid = max(base_bid, highest_prev_bid + 2)
        
        # If all opponents bid very low and supply is good, we can save money
        if all(bid < DAILY_SALARY * 0.5 for bid in yesterday_bids) and supply >= total_water_required_by_all:
            base_bid = min(base_bid, DAILY_SALARY * 0.45)

    # Final bid must be within budget and non-negative
    final_bid = min(my_status['budget'], base_bid)
    
    # Ensure a strong bid if HP is critically low
    if my_status['hp'] <= 1 and final_bid < DAILY_SALARY * 0.7:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.7)

    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to get water and save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Default bid if no previous bids or for base case
    # Adjust default bid based on my HP if no previous bids are available
    if not yesterday_bids:
        if my_status['hp'] <= 2: # Critical health
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        elif my_status['hp'] <= 4: # Struggling health
            return min(my_status['budget'], DAILY_SALARY * 0.75)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.55)

    # Logic based on yesterday's highest bid from active opponents
    highest_prev_bid = max(yesterday_bids)

    # Aggressive opponent behavior (highest bid was very high, similar to example threshold)
    if highest_prev_bid >= DAILY_SALARY * 0.85: 
        if my_status['hp'] > 3: # Good HP, can take a slight risk to save budget
            return min(my_status['budget'], DAILY_SALARY * 0.3)
        else: # Low HP, must bid aggressively to survive
            return min(my_status['budget'], DAILY_SALARY * 0.95)
    # Moderate or conservative opponent behavior
    else:
        # Calculate total water demand vs. supply to gauge competition
        total_water_demand = sum([o['water_requirement'] for o in alive_opponents]) + WATER_REQ
        
        # If supply is tight (less than total demand), be more competitive
        if day_context['supply'] < total_water_demand:
            # Bid slightly above highest previous bid, but ensure it's at least a decent amount
            return min(my_status['budget'], max(DAILY_SALARY * 0.6, highest_prev_bid + 5))
        # If supply is ample, adjust based on my HP
        else:
            # If my HP is very good, try to bid more conservatively
            if my_status['hp'] > 6:
                return min(my_status['budget'], max(DAILY_SALARY * 0.4, highest_prev_bid * 0.9))
            # Otherwise, bid slightly above previous to secure water
            else:
                return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 2))
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

    bid_amount = DAILY_SALARY * 0.55

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                bid_amount = DAILY_SALARY * 0.3
            else:
                bid_amount = DAILY_SALARY * 0.95
        else:
            bid_amount = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)
    else:
        if my_status['hp'] <= 2:
            bid_amount = DAILY_SALARY * 0.9
        else:
            bid_amount = DAILY_SALARY * 0.55

    return min(my_status['budget'], bid_amount)
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
    
    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    remaining_days = EPISODE_DAYS - day_context['day']

    if my_status['hp'] <= 2 or remaining_days <= 2:
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        bid = DAILY_SALARY * 0.85
    else:
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            bid = max(DAILY_SALARY * 0.8, highest_prev_bid + 5.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            bid = max(DAILY_SALARY * 0.7, highest_prev_bid + 2.0)
        else:
            bid = DAILY_SALARY * 0.65
    
    final_bid = min(my_status['budget'], bid)
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_DAYS = 10

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimal to get water and save budget
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Get yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a target bid based on my status and game phase
    target_bid_percentage = 0.5 # Default moderate bid percentage

    if my_hp <= 3 or my_no_water_days >= 1:
        target_bid_percentage = 0.98 # Very high for survival
    elif current_day >= MAX_DAYS - 2: # Last few days, push hard
        target_bid_percentage = 0.95
    elif my_hp <= 5: # Medium low HP
        target_bid_percentage = 0.85
    else: # Healthy HP
        if current_day < MAX_DAYS / 2: # Early game
            target_bid_percentage = 0.65
        else: # Mid game
            target_bid_percentage = 0.75

    # Convert percentage to actual bid amount
    calculated_bid = DAILY_SALARY * target_bid_percentage

    # Adjust bid based on yesterday's highest opponent bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents are bidding high, ensure our bid is competitive
        # Add a small buffer to try and outbid
        calculated_bid = max(calculated_bid, highest_prev_bid + (DAILY_SALARY * 0.03)) # 3% buffer

    # Ensure bid is not too low
    calculated_bid = max(calculated_bid, 1.0)

    # Final bid is limited by budget
    final_bid = min(my_budget, calculated_bid)

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

    # If no opponents, bid minimum to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_bid = 0.0

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If highest previous bid was very high, react based on my HP
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # If HP is good, try to save
                current_bid = DAILY_SALARY * 0.3
            else: # If HP is bad, bid high to survive
                current_bid = DAILY_SALARY * 0.95
        else: # Highest previous bid was moderate or low
            # Try to bid slightly above it, but not overpay
            current_bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)
    else: # No previous bids from opponents or first day
        if my_status['hp'] <= 2: # Critical HP
            current_bid = DAILY_SALARY * 0.9
        elif my_status['no_water_days'] > 0: # About to lose HP
            current_bid = DAILY_SALARY * 0.8 # Bid high to prevent HP loss
        else: # Normal situation
            # Consider supply vs demand for initial bid
            num_my_slots = int(day_context['supply'] // WATER_REQ)
            num_competitors = len(alive_opponents) + 1
            if num_my_slots < num_competitors: # Tight competition
                current_bid = DAILY_SALARY * 0.7
            else: # Abundant supply or just myself
                current_bid = DAILY_SALARY * 0.55

    # Ensure the bid is always positive and within budget
    final_bid = max(1.0, min(my_status['budget'], current_bid))
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    
    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Initialize bid based on HP and remaining budget
    bid_multiplier = 0.65 # Default for healthy HP
    
    if my_hp <= 2: # Critical HP
        bid_multiplier = 0.98
    elif my_hp <= 4: # Low HP
        bid_multiplier = 0.90
    elif my_hp <= 6: # Medium HP
        bid_multiplier = 0.80
    elif my_hp <= 8: # Slightly below full HP
        bid_multiplier = 0.70
    
    base_bid = DAILY_SALARY * bid_multiplier

    # Adjust based on remaining days - become more aggressive towards the end
    days_remaining = EPISODE_DAYS - current_day
    if days_remaining <= 3 and my_hp < 10: # Late game, need to survive
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif days_remaining <= 1 and my_hp < 10: # Very late game, highest bid
        base_bid = DAILY_SALARY * 0.99 # Almost max bid to survive last day

    # Opponent analysis from previous day
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Default to current base_bid if no previous bids or specific conditions not met
    adjusted_bid_from_opponents = base_bid 

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)
        
        if my_hp < 10: # I need water, be aggressive
            # If max opponent bid was significantly higher, bid slightly above it
            if max_yesterday_bid > adjusted_bid_from_opponents:
                adjusted_bid_from_opponents = max(adjusted_bid_from_opponents, max_yesterday_bid + 5)
            # If average opponent bid was higher, try to outbid average
            elif avg_yesterday_bid > adjusted_bid_from_opponents:
                adjusted_bid_from_opponents = max(adjusted_bid_from_opponents, avg_yesterday_bid + 2)
            
            # If very critical HP, ensure a very high bid
            if my_hp <= 2:
                adjusted_bid_from_opponents = max(adjusted_bid_from_opponents, DAILY_SALARY * 0.99)
        else: # I am at full HP, can be more strategic
            # If max bid was high, I should also bid high enough to win some water
            if max_yesterday_bid > DAILY_SALARY * 0.75: # If max bid was above 112.5
                adjusted_bid_from_opponents = max(adjusted_bid_from_opponents, max_yesterday_bid * 0.9 + 1) # Bid slightly below max, but try to win
            elif avg_yesterday_bid > DAILY_SALARY * 0.65: # If avg bid was above 97.5
                adjusted_bid_from_opponents = max(adjusted_bid_from_opponents, avg_yesterday_bid + 1) # Bid slightly above avg
            else: # Bids were generally low, stick to my base or slightly lower if very healthy
                adjusted_bid_from_opponents = min(adjusted_bid_from_opponents, DAILY_SALARY * 0.6) # Conserve budget
    
    # Combine base_bid with opponent-adjusted bid, taking the higher one if it makes sense
    base_bid = max(base_bid, adjusted_bid_from_opponents)

    # Adjust based on supply relative to number of competitors
    # If current_supply is at the lower end of the range, increase bid
    if current_supply <= (MIN_SUPPLY + MAX_SUPPLY) / 2 and my_hp < 10: # Supply is below average and I need water
        base_bid *= 1.05 # Increase bid slightly
    elif current_supply <= (MIN_SUPPLY + MAX_SUPPLY) / 2 and my_hp == 10: # Supply is below average even if healthy
        base_bid *= 1.02 # Increase bid slightly to stay competitive

    # Final bid must not exceed budget
    final_bid = min(my_budget, base_bid)
    
    # Ensure bid is at least 1 if I need water and have budget
    if my_hp < 10 and final_bid < 1.0 and my_budget > 0:
        final_bid = 1.0

    # Ensure bid is not negative
    return max(0.0, final_bid)
"""
