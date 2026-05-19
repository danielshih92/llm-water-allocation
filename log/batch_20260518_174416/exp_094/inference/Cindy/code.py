# ============================================================
# Experiment: exp_094
# Agent: Cindy
# Source: exp_094
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    my_water_requirement = 13
    my_daily_salary = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], my_daily_salary * 0.1)

    # Base bid strategy: competitive but not over-aggressive initially
    bid = my_daily_salary * 0.5

    # 1. Survival instinct: If HP is low, bid aggressively
    if my_status['hp'] <= 2: # Critical HP
        bid = my_daily_salary * 0.95
    elif my_status['hp'] == 3: # Low HP
        bid = my_daily_salary * 0.8
    elif my_status['hp'] == 4: # Moderate HP, but still cautious
        bid = my_daily_salary * 0.7

    # 2. Adjust based on opponent's yesterday bids (if available)
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents were very aggressive yesterday
        if highest_prev_bid >= my_daily_salary * 0.8:
            if my_status['hp'] <= 3: # If my HP is low/critical, I must secure water
                bid = max(bid, my_daily_salary * 0.98) # Bid very high for survival
            else: # My HP is good, but competition is high. Try to outbid slightly.
                bid = max(bid, highest_prev_bid + 2)
        # If opponents were moderately aggressive
        elif highest_prev_bid >= my_daily_salary * 0.5:
            if my_status['hp'] <= 4: # If my HP is not great, be competitive
                bid = max(bid, highest_prev_bid + 1)
            else: # My HP is good, try to get it cheaper but still above average
                bid = max(bid, avg_prev_bid * 1.05)
        # If opponents bid low yesterday, and my HP is good, try to save money
        elif highest_prev_bid < my_daily_salary * 0.4 and my_status['hp'] > 4:
            bid = min(bid, my_daily_salary * 0.35)

    # 3. Adjust based on current supply and number of opponents
    current_supply = day_context['supply']
    
    # Calculate how many full water requirements can be met from current supply
    # For supply_range [15, 25] and water_requirement 13, this is typically 1.
    num_possible_full_shares = int(current_supply // my_water_requirement)
    if num_possible_full_shares == 0: # Should not happen with current supply range
        num_possible_full_shares = 1 

    # If competition for full shares is high (more agents than available full shares)
    if num_alive_opponents + 1 > num_possible_full_shares: # +1 includes myself
        if my_status['hp'] <= 3: # Critical or low HP, must win
            bid = max(bid, my_daily_salary * 0.9)
        elif my_status['hp'] > 3: # Not critical, but still competitive
            bid = max(bid, my_daily_salary * 0.6 + (my_daily_salary * 0.05 * num_alive_opponents))

    # If supply is relatively abundant and competition low, try to save money
    if num_alive_opponents < num_possible_full_shares and my_status['hp'] > 4:
        bid = min(bid, my_daily_salary * 0.3)

    # Ensure bid is not negative or zero, and has a reasonable floor
    bid = max(5.0, bid)

    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], bid)

    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid conservatively to survive and save money
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid
    base_bid = DAILY_SALARY * 0.55 # A moderate bid

    # Adjust bid based on my HP and no_water_days
    if my_status['hp'] <= 2: # Critical HP, must get water
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP, prioritize water
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    elif my_status['no_water_days'] >= 1: # Missed water yesterday, need it today
        base_bid = max(base_bid, DAILY_SALARY * 0.9)

    # Adjust bid based on supply
    supply = day_context['supply']
    if supply <= WATER_REQ: # Very low supply, high competition
        base_bid = max(base_bid, DAILY_SALARY * 0.9) # Ensure high bid
    elif supply < 2 * WATER_REQ: # Tight supply for multiple agents
        base_bid = max(base_bid, DAILY_SALARY * 0.7) # Increase bid to compete
    else: # Abundant supply
        base_bid = min(base_bid, DAILY_SALARY * 0.6) # Can afford to be more conservative if not critical

    # Adjust bid based on yesterday's opponent bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents were very aggressive
            if my_status['hp'] > 3: # If healthy, can try to outlast or bid slightly higher
                base_bid = max(base_bid, highest_prev_bid + 5)
            else: # If not healthy, must compete strongly
                base_bid = max(base_bid, DAILY_SALARY * 0.9)
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderate aggression
            base_bid = max(base_bid, highest_prev_bid + 1.5)
        else: # Opponents were conservative
            base_bid = min(base_bid, highest_prev_bid + 1) # Try to win cheaply, but ensure it's not too low

    # If it's the last day and I need water, bid everything
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days == 0 and my_status['hp'] <= 4:
        base_bid = my_status['budget']

    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure bid is at least 0.0
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid calculation
    base_bid = DAILY_SALARY * 0.5 # Start with a moderate bid

    # Adjust based on my HP
    if my_status['hp'] <= 2: # Critical HP, bid very aggressively
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5: # Low HP, bid aggressively
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    elif my_status['hp'] > 8: # Healthy, can afford to be slightly less aggressive or maintain
        base_bid = min(base_bid, DAILY_SALARY * 0.6) # Don't overspend if not necessary

    # Adjust based on opponent's previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were very aggressive, I need to react
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, highest_prev_bid + 5) # Try to outbid
        elif highest_prev_bid <= DAILY_SALARY * 0.3: # If opponents were conservative, try to get water cheaper
            base_bid = min(base_bid, highest_prev_bid + 1) # Just slightly above
        else: # Moderate competition, bid slightly above to win
            base_bid = max(base_bid, highest_prev_bid + 2)

    # Adjust based on supply scarcity (number of players vs. water available)
    if num_alive_opponents > 0: # Only if there are other players to compete with
        # Estimate total water needed if everyone wanted full requirement
        total_water_needed_for_all = (num_alive_opponents + 1) * WATER_REQ 
        
        if day_context['supply'] < total_water_needed_for_all * 0.7: # Very scarce supply
            # If supply is very low, it's a fight for survival. Bid higher if HP is not perfect.
            if my_status['hp'] < 10:
                base_bid = max(base_bid, DAILY_SALARY * 0.85)

        elif day_context['supply'] < total_water_needed_for_all: # Scarce, but not extremely
            if my_status['hp'] < 8:
                base_bid = max(base_bid, DAILY_SALARY * 0.7)

    # Ensure the bid does not exceed the current budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure a minimum bid if I desperately need water and have budget
    if not alive_opponents: # If I am the only one left
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.1) # Bid low to secure water
        if final_bid == 0 and my_status['budget'] > 0: 
            final_bid = 1.0 # Bid minimum to get water if budget allows

    elif my_status['hp'] < 10 and final_bid == 0 and my_status['budget'] > 0:
        # If I need water (HP not full) and my calculated bid is 0 but I have budget, bid a minimum amount
        final_bid = max(1.0, min(my_status['budget'], DAILY_SALARY * 0.1))

    return final_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If I'm the only one left, bid minimally to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        # Ensure 'bid' is checked before access, and 'previous_trace' exists
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Decision logic based on yesterday's highest pressure and my HP
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If yesterday's highest bid was very high, react
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If healthy, try to conserve budget by bidding lower (risky, but saves money)
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            # If low HP, bid very aggressively to survive
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        
        # If yesterday's bids were moderate, bid slightly above the highest
        return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
    
    # If no previous bids (e.g., Day 1 or all previous opponents died/had no trace)
    if my_status['hp'] <= 2: # Critical HP, bid aggressively
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    
    # Default bid for healthy state or no strong previous bid signal
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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return max(1.0, min(my_budget, DAILY_SALARY * 0.1))

    yesterday_bids = []
    opponent_desperation_score = 0

    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
            
            if opp_data['hp'] <= 2:
                opponent_desperation_score += 2
            elif opp_data['hp'] <= 5:
                opponent_desperation_score += 1

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    base_bid = DAILY_SALARY * 0.6 

    if my_hp <= 2:
        base_bid = DAILY_SALARY * 1.2
    elif my_hp <= 4:
        base_bid = DAILY_SALARY * 1.0
    elif my_hp <= 7:
        base_bid = DAILY_SALARY * 0.8
    else:
        base_bid = DAILY_SALARY * 0.65

    if current_day >= EPISODE_DAYS - 2:
        base_bid *= 1.2
    elif current_day <= 3:
        if my_hp > 7:
            base_bid *= 0.85

    if current_supply <= WATER_REQ + 2:
        base_bid *= 1.1
    elif current_supply >= WATER_REQ * 1.5:
        if my_hp > 5:
            base_bid *= 0.95

    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            if my_hp <= 5:
                base_bid = max(base_bid, highest_prev_bid + 5)
            else:
                base_bid = max(base_bid, highest_prev_bid * 0.95)
        elif highest_prev_bid >= DAILY_SALARY * 0.7:
            base_bid = max(base_bid, highest_prev_bid + 2)
        else:
            base_bid = max(base_bid, highest_prev_bid + 1)

    if len(alive_opponents) > 0 and opponent_desperation_score >= len(alive_opponents):
        if my_hp <= 5:
            base_bid *= 1.15
        elif my_hp > 7:
            base_bid *= 0.9

    final_bid = max(1.0, min(base_bid, my_budget))

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    max_possible_winners = int(day_context['supply'] // WATER_REQ)
    if max_possible_winners == 0: 
        max_possible_winners = 1 

    num_competitors = len(alive_opponents)

    bid_factor = 0.55 
    bid_amount_from_prev = 0.0

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if max_possible_winners <= 1: 
            if my_status['hp'] <= 3: 
                bid_factor = 0.95
            else: 
                bid_factor = 0.80
            bid_amount_from_prev = highest_prev_bid + 5.0
        elif max_possible_winners >= num_competitors + 1: 
            bid_factor = 0.40
            bid_amount_from_prev = highest_prev_bid + 1.0
        else: 
            if my_status['hp'] <= 2: 
                bid_factor = 0.90
            elif my_status['hp'] <= 5: 
                bid_factor = 0.75
            else: 
                bid_factor = 0.65
            bid_amount_from_prev = highest_prev_bid + 2.0
        
        bid_amount = max(DAILY_SALARY * bid_factor, bid_amount_from_prev)
    else: 
        if my_status['hp'] <= 2:
            bid_factor = 0.9
        else:
            bid_factor = 0.55
        bid_amount = DAILY_SALARY * bid_factor

    if my_status['hp'] <= 1:
        bid_amount = DAILY_SALARY * 0.99
    elif my_status['hp'] <= 3:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.9)

    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] > 0:
        required_budget_for_survival = DAILY_SALARY * (remaining_days + 1)
        if my_status['budget'] >= required_budget_for_survival:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.85)
        elif my_status['hp'] <= 3: 
             bid_amount = max(bid_amount, DAILY_SALARY * 0.98)

    final_bid = min(bid_amount, my_status['budget'])
    
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid minimally to get water and save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid: slightly above Eric's historically observed low bid (15.0 for his total requirement)
    base_bid_amount = 16.0 

    # Determine bid based on critical health or no water days
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        # Bid aggressively to survive
        current_bid = min(my_status['budget'], DAILY_SALARY * 0.95)
        if yesterday_bids:
            current_bid = max(current_bid, max(yesterday_bids) + 2.0)
        return current_bid

    # Adjust bid for the end of the episode
    if day_context['day'] >= EPISODE_DAYS - 2:
        # Be more aggressive as budget is less critical for future rounds
        current_bid = min(my_status['budget'], DAILY_SALARY * 0.8)
        if yesterday_bids:
            current_bid = max(current_bid, max(yesterday_bids) + 1.0)
        return current_bid

    # Normal bidding strategy
    if yesterday_bids:
        max_opp_bid = max(yesterday_bids)
        
        # If max opponent bid is low, try to win by bidding slightly higher
        if max_opp_bid < DAILY_SALARY * 0.3: # Low competition
            current_bid = max(base_bid_amount, max_opp_bid + 1.5)
        elif max_opp_bid < DAILY_SALARY * 0.6: # Moderate competition
            current_bid = max(base_bid_amount, max_opp_bid + 1.0)
        else: # High competition
            if my_status['hp'] > 5: # Healthy, conserve budget
                current_bid = min(my_status['budget'], DAILY_SALARY * 0.4)
            else: # Not critical, but not perfectly healthy, try to compete
                current_bid = max(base_bid_amount, max_opp_bid + 0.5)
    else:
        # No previous bids from alive opponents (e.g., Day 1 or all others died)
        current_bid = base_bid_amount # Start with the base bid

    # Ensure bid doesn't exceed budget
    # Ensure bid is at least a minimal amount (10% of daily salary) to be competitive
    min_viable_bid = DAILY_SALARY * 0.1
    final_bid = min(my_status['budget'], max(min_viable_bid, current_bid))
    
    # If not in critical condition, cap bid at DAILY_SALARY to ensure profitability
    if my_status['hp'] > 2 and my_status['no_water_days'] == 0:
        final_bid = min(final_bid, DAILY_SALARY)

    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            else:
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else:
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))

    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    else:
        return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to get water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid based on my HP and no_water_days
    # Prioritize survival
    if my_status['hp'] <= WATER_REQ: # Critical HP
        my_bid = DAILY_SALARY * 0.98
    elif my_status['no_water_days'] > 0: # Missed water, need to recover
        my_bid = DAILY_SALARY * 0.90
    elif my_status['hp'] <= WATER_REQ * 2: # Low HP
        my_bid = DAILY_SALARY * 0.75
    else: # Healthy HP
        my_bid = DAILY_SALARY * 0.55 # Moderate bid to save money but still compete

    # Adjust bid based on opponent's previous behavior if available
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest bid was very high, and I need water (not very high HP), bid above it
        if highest_prev_bid >= DAILY_SALARY * 0.85: # Very high competition
            if my_status['hp'] <= WATER_REQ * 3 or my_status['no_water_days'] > 0:
                my_bid = max(my_bid, highest_prev_bid + 3.0) # Outbid aggressive opponents
            else: # High HP, can try to save, but don't drop too low
                my_bid = min(my_bid, DAILY_SALARY * 0.4) # Try to save if not desperate
        # If highest bid was moderate, adjust
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderate competition
            if my_status['hp'] <= WATER_REQ * 2 or my_status['no_water_days'] > 0:
                my_bid = max(my_bid, highest_prev_bid + 1.0) # Slightly outbid
            else:
                my_bid = min(my_bid, highest_prev_bid * 0.95) # Try to get it cheaper
        else: # Bids were generally low
            if my_status['hp'] > WATER_REQ * 3 and my_status['no_water_days'] == 0:
                my_bid = min(my_bid, DAILY_SALARY * 0.4) # Bid low to save
            else:
                my_bid = max(my_bid, DAILY_SALARY * 0.45) # Ensure I get water if I need it

    # Consider supply: if supply is very low (e.g., only enough for one player), competition is higher
    # My WATER_REQ is 13.
    if day_context['supply'] <= WATER_REQ + 2 and (my_status['hp'] <= WATER_REQ * 2 or my_status['no_water_days'] > 0):
        my_bid *= 1.05 # Slightly increase bid if supply is very tight and I need water

    # Ensure bid is not negative or zero, and within budget
    my_bid = max(1.0, my_bid) # Minimum bid to always participate
    my_bid = min(my_status['budget'], my_bid)

    return round(my_bid, 2)
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
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    base_bid = DAILY_SALARY * 0.5
    if current_day > EPISODE_DAYS / 2:
        base_bid = DAILY_SALARY * 0.65

    if my_hp <= 2 or my_no_water_days > 0:
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    highest_prev_bid = 0.0
    num_desperate_opponents = 0

    for opp in alive_opponents:
        if opp['hp'] <= 2 or opp['no_water_days'] > 0:
            num_desperate_opponents += 1
        
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])

    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, highest_prev_bid * 1.05)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            base_bid = max(base_bid, highest_prev_bid + (DAILY_SALARY * 0.05))
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.55)

    if num_desperate_opponents > 0:
        base_bid = max(base_bid, DAILY_SALARY * (0.7 + num_desperate_opponents * 0.05))
        base_bid = min(base_bid, DAILY_SALARY * 0.98)

    total_water_needed_by_alive = WATER_REQ + sum(o['water_requirement'] for o in alive_opponents)
    
    if current_supply < total_water_needed_by_alive:
        supply_shortage_ratio = (total_water_needed_by_alive - current_supply) / total_water_needed_by_alive
        base_bid *= (1 + supply_shortage_ratio * 0.3)

    final_bid = min(my_budget, base_bid)
    final_bid = max(final_bid, DAILY_SALARY * 0.05)

    return final_bid
"""
