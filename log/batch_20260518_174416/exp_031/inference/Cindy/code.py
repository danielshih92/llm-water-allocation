# ============================================================
# Experiment: exp_031
# Agent: Cindy
# Source: exp_031
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

    # Base bid strategy
    # Start with a moderate bid
    bid = DAILY_SALARY * 0.6

    # Adjust based on my HP
    if my_status['hp'] <= 2:  # Critical health (2 days without water)
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low health (1 day without water)
        bid = DAILY_SALARY * 0.75
    elif my_status['hp'] >= 8: # Healthy, can afford to save
        bid = DAILY_SALARY * 0.45

    # Adjust based on supply scarcity
    # Supply is 15-25. If supply is low, increase bid. If high, decrease bid.
    # Normalized supply: 0 for MIN_SUPPLY, 1 for MAX_SUPPLY
    supply_normalized = (day_context['supply'] - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    # If supply_normalized is 0 (min supply), adjustment is positive (increase bid)
    # If supply_normalized is 1 (max supply), adjustment is negative (decrease bid)
    # Range of adjustment: +/- 20% of daily salary
    supply_adjustment = (0.5 - supply_normalized) * (DAILY_SALARY * 0.2)
    bid += supply_adjustment

    # Adjust based on yesterday's opponent bids (exploiting previous_trace)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If highest bid was very high, we might need to bid higher to compete
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] <= 4: # If I need water, bid aggressively to win
                bid = max(bid, highest_prev_bid + 5.0)
            else: # If healthy, try to outbid slightly to win, but don't overspend
                bid = max(bid, highest_prev_bid + 1.0)
        # If highest bid was moderate, try to secure water without overpaying too much
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            if my_status['hp'] <= 6: # If I need water or am neutral, try to win
                bid = max(bid, highest_prev_bid + 2.0)
            # else (healthy): current bid is already moderate/low, no need to increase based on moderate bids
        # If highest bid was low, we can probably get water cheaper
        else: # highest_prev_bid < DAILY_SALARY * 0.5
            bid = min(bid, highest_prev_bid + 1.0) # Try to win at a lower cost, but secure it

    # Ensure bid is not negative and within budget
    bid = max(1.0, bid) # Minimum bid of 1
    bid = min(my_status['budget'], bid)

    return bid
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
    
    # If no opponents, bid low to win and save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1) 

    # Base bid: Start with a strong bid. Meta-round context shows high bids are needed.
    # Aim for a bid that is competitive, around the salary.
    current_bid_target = DAILY_SALARY * 0.95 # Base at 142.5

    # Adjust target bid based on my current HP
    if my_status['hp'] <= 2: # Very desperate
        current_bid_target = DAILY_SALARY * 1.05 # Bid very high, potentially above salary
    elif my_status['hp'] <= 4: # Getting desperate
        current_bid_target = DAILY_SALARY * 1.0 # Bid full salary
    elif my_status['hp'] <= 6: # Moderate HP
        current_bid_target = DAILY_SALARY * 0.95
    # If my_status['hp'] is 7 or 8, current_bid_target remains DAILY_SALARY * 0.95

    # Incorporate opponent's yesterday's bids from previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        
        # If I need water (HP not full), I must aim to beat the highest bid from yesterday.
        if my_status['hp'] < 8: # If not at full HP, need to win water
            current_bid_target = max(current_bid_target, max_yesterday_bid + 1)
        else: # At full HP, can afford to be slightly less aggressive, but still competitive
            if max_yesterday_bid > DAILY_SALARY * 0.8: # Opponents are competitive
                current_bid_target = max(current_bid_target, max_yesterday_bid * 0.98) # Stay very close
            else: # Opponents were bidding lower, try to win cheaper
                current_bid_target = min(current_bid_target, max_yesterday_bid + 5, DAILY_SALARY * 0.85)

    # Adjust for day progression: increase aggression towards end of episode if HP is low
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 3 and my_status['hp'] <= 3: # Last few days, need to survive
        current_bid_target = max(current_bid_target, DAILY_SALARY * 1.15) # Very aggressive bid

    # Final bid cannot exceed current budget
    final_bid = min(my_status['budget'], current_bid_target)
    
    # Ensure a minimal bid of 1.0 to participate
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If I am the only one left, bid minimally to get water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_supply = day_context['supply']
    
    # Determine bid based on previous day's bids and current status
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # Critical HP: Bid very aggressively to secure water
        if my_status['hp'] <= 3:
            return min(my_status['budget'], DAILY_SALARY * 0.99)
        
        # Water scarcity check: If supply is below average, competition is higher
        if current_supply < (MIN_SUPPLY + MAX_SUPPLY) / 2: # Supply is below 20
            if my_status['hp'] <= 6: # Moderate to low HP, bid very high
                return min(my_status['budget'], max(DAILY_SALARY * 0.9, highest_prev_bid + 5))
            else: # Good HP, but still competitive due to scarcity
                return min(my_status['budget'], max(DAILY_SALARY * 0.85, highest_prev_bid + 3))

        # General strategy based on highest previous bid and my HP
        if highest_prev_bid >= DAILY_SALARY * 0.85: # High pressure (e.g., Alex/Bob likely)
            if my_status['hp'] > 5: # Good HP, try to be competitive but save
                return min(my_status['budget'], max(DAILY_SALARY * 0.75, highest_prev_bid + 1.5))
            else: # Moderate to low HP, bid to win
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        
        elif highest_prev_bid >= DAILY_SALARY * 0.65: # Moderate pressure (e.g., David or others)
            if my_status['hp'] <= 4: # Low HP, bid high
                return min(my_status['budget'], max(DAILY_SALARY * 0.88, highest_prev_bid + 3))
            else: # Good HP, bid slightly above to win
                return min(my_status['budget'], max(DAILY_SALARY * 0.7, highest_prev_bid + 2))
        
        else: # Low pressure (highest_prev_bid < 0.65 * DAILY_SALARY)
            if my_status['hp'] <= 2: # Very low HP, don't risk it
                return min(my_status['budget'], DAILY_SALARY * 0.9)
            # If HP is good, try to get water cheaply, but ensure winning
            return min(my_status['budget'], max(DAILY_SALARY * 0.55, highest_prev_bid + 1))

    # Default bid if no yesterday_bids (e.g., Day 1 or all opponents are new)
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.9) # Be aggressive if HP starts low
    elif num_alive_opponents >= 2: # Multiple opponents, bid competitively
        return min(my_status['budget'], DAILY_SALARY * 0.8)
    else: # One opponent, or default competitive bid
        return min(my_status['budget'], DAILY_SALARY * 0.7)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply'] # Not directly used for indexing, so int() not needed here

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        return min(my_current_budget, DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            # Only consider bids that were actually made (non-zero)
            if prev_trace['bid'] > 0:
                yesterday_bids.append(prev_trace['bid'])

    # Base bid strategy, informed by successful past meta-round performance (e.g., Eric's ~64-70)
    base_bid = DAILY_SALARY * 0.45 # Approximately 67.5

    # Adjust bid based on opponent activity from previous_trace
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

        if max_yesterday_bid >= DAILY_SALARY * 0.6: # If max bid was high (e.g., >= 90)
            base_bid = max(base_bid, max_yesterday_bid + 5) # Try to outbid by a small margin
        elif max_yesterday_bid > 0: # Opponents made some bids, but not extremely high
            base_bid = max(base_bid, max_yesterday_bid + 1) # Just slightly outbid

    # Adjust bid based on my HP for survival
    # Critical HP: will die next day without water
    if my_current_hp <= WATER_REQ:
        base_bid = max(base_bid, DAILY_SALARY * 0.95) # Bid very aggressively
    # Low HP: can survive one more day without water
    elif my_current_hp <= 2 * WATER_REQ:
        base_bid = max(base_bid, DAILY_SALARY * 0.75) # Bid aggressively

    # Consider the day number for late-game aggression if needed
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_current_hp <= 3 * WATER_REQ: # Last few days, need to ensure survival
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    # Ensure bid does not exceed current budget
    final_bid = min(my_current_budget, base_bid)

    # Ensure a minimum positive bid if budget allows and it's not zero due to budget constraint
    if final_bid < 1.0 and my_current_budget > 0:
        final_bid = min(my_current_budget, 1.0)
    
    # If budget is 0, cannot bid
    if my_current_budget <= 0:
        return 0.0

    return final_bid
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
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid a minimal amount to save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], 1.0)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']

    bid = 0.0

    # CRITICAL: If I'm about to die, bid very high
    if my_current_hp <= 2:
        bid = max(max_yesterday_bid + 15, DAILY_SALARY * 1.2)
    elif my_current_hp <= 5: # Low HP, need water soon
        bid = max(max_yesterday_bid + 10, DAILY_SALARY * 1.0)
    # If budget is low, try to conserve, but still fight if HP is not super high
    elif my_current_budget < DAILY_SALARY * 2:
        if my_current_hp > 7: # Can afford to lose a day to save
            bid = DAILY_SALARY * 0.5
        else: # Still need to fight
            bid = max(max_yesterday_bid + 5, DAILY_SALARY * 0.8)
    # General strategy for healthy HP
    else:
        if num_alive_opponents > 2:
            bid = max(max_yesterday_bid + 5, DAILY_SALARY * 0.9)
        elif num_alive_opponents == 1:
            bid = max(max_yesterday_bid + 2, DAILY_SALARY * 0.8)
        else: # 2 opponents
            bid = max(max_yesterday_bid + 1, DAILY_SALARY * 0.75)

    return min(my_current_budget, bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Calculate available water slots based on my water requirement
    # CRITICAL INDEX RULE: Ensure int conversion for discrete counts
    num_slots = int(day_context['supply'] / WATER_REQ)

    # Collect yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    # Base bid - a reasonable starting point
    base_bid = DAILY_SALARY * 0.5

    # Initialize bid
    bid = base_bid

    # Adjust bid based on my HP and competition
    if my_status['hp'] <= 2: # Critical HP, must get water
        bid = max(base_bid * 1.5, max_yesterday_bid + 15) # Bid very aggressively
        bid = max(bid, DAILY_SALARY * 0.95) # Ensure it's at least 95% of salary
    elif my_status['hp'] <= 4: # Low HP, need water
        bid = max(base_bid * 1.2, max_yesterday_bid + 10)
        bid = max(bid, DAILY_SALARY * 0.8)
    else: # Healthy HP, can be more strategic
        if len(alive_opponents) == 0: # No opponents
            bid = DAILY_SALARY * 0.05 # Very low bid to save budget
        elif num_slots > len(alive_opponents): # More slots than active players (including me if I get one)
            # Enough water for everyone, so bid conservatively
            bid = min(base_bid * 0.8, max_yesterday_bid + 2) # Try to get it cheap
            bid = max(bid, DAILY_SALARY * 0.1) # Minimum bid if no high competition
        else: # Normal or high competition (slots <= active players)
            bid = max(base_bid, max_yesterday_bid + 5) # Slightly above yesterday's max to win
            bid = min(bid, DAILY_SALARY * 0.85) # Cap bid to avoid overspending if not critical

    # Ensure bid doesn't exceed budget
    final_bid = min(bid, my_status['budget'])

    # Ensure bid is at least 1 if budget allows and I need water
    if final_bid <= 0 and my_status['budget'] > 0 and my_status['hp'] <= 5: 
        final_bid = 1.0 

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

    # If no opponents remain, bid very low to maximize budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Determine how many players can potentially get their full water requirement
    # Note: day_context['supply'] is float, so explicit int() for division
    num_possible_winners = int(day_context['supply'] // WATER_REQ)

    # If supply is less than my requirement, I cannot get water. Bid minimum to save budget.
    if num_possible_winners == 0:
        return 0.01

    # Base bid strategy: Start aggressive due to overall scarcity in the game
    base_bid = DAILY_SALARY * 0.85 # Default aggressive bid

    # Adjust bid based on my health (HP) and consecutive days without water
    if my_status['no_water_days'] >= 1 or my_status['hp'] <= 3:
        # Critical state: must secure water, bid very high
        base_bid = DAILY_SALARY * 0.99
    elif my_status['hp'] >= 8 and my_status['budget'] > DAILY_SALARY * (EPISODE_DAYS - day_context['day'] + 2):
        # Good health and sufficient budget: can be slightly less aggressive if water is not extremely scarce
        # But given the typical scarcity, still need to be competitive
        if num_possible_winners >= len(alive_opponents) + 1: # If enough for everyone (rare)
             base_bid = DAILY_SALARY * 0.65
        else: # Still competitive, but not desperate
             base_bid = DAILY_SALARY * 0.8

    # Analyze opponent's previous bids and adjust strategy
    competitive_bids_normalized = [] # Store bids normalized by opponent's salary, then converted to my salary equivalent
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            opp_salary = opp['daily_salary']
            if opp_salary == 0: # Prevent division by zero, assume a reasonable salary if not set
                opp_salary = DAILY_SALARY # Default to my salary

            # Normalize opponent's bid by their salary to understand their 'aggressiveness'
            bid_ratio = prev['bid'] / opp_salary

            # If they won the bid, or bid a significant portion of their salary, consider it a competitive bid
            # Convert their bid strength to an equivalent bid for my salary
            if prev.get('status') == 'won_bid' or bid_ratio > 0.7:
                competitive_bids_normalized.append(bid_ratio * DAILY_SALARY)

    if competitive_bids_normalized:
        highest_competitive_bid = max(competitive_bids_normalized)
        average_competitive_bid = sum(competitive_bids_normalized) / len(competitive_bids_normalized)

        # If the highest competitive bid was very high (relative to my salary)
        if highest_competitive_bid >= DAILY_SALARY * 0.9:
            # If I'm in a critical state, I need to outbid the highest previous bid
            if my_status['no_water_days'] >= 1 or my_status['hp'] <= 3:
                base_bid = max(base_bid, highest_competitive_bid + 5) # Bid slightly higher
            else:
                # Otherwise, stay competitive but try not to overspend unnecessarily
                base_bid = max(base_bid, average_competitive_bid + 2) # Bid slightly above average
        elif highest_competitive_bid > DAILY_SALARY * 0.7: # Moderately high competitive bids
            base_bid = max(base_bid, highest_competitive_bid + 1) # Try to slightly outbid

    # Ensure the final bid is positive and does not exceed current budget
    final_bid = min(my_status['budget'], base_bid)
    return max(0.01, final_bid)
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
        return min(my_status['budget'], 1.0)

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

    if my_status['hp'] <= 2:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.95)

    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] <= 3:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.8)

    if day_context['supply'] < (len(alive_opponents) + 1) * WATER_REQ * 1.2:
        bid_amount *= 1.1

    final_bid = min(my_status['budget'], bid_amount)
    final_bid = max(1.0, final_bid)

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

    # If no opponents, bid low to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Base bid strategy: Start with a competitive bid
    my_bid = DAILY_SALARY * 0.75 # 112.5

    # React to highest previous bid from any alive opponent
    highest_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])

    if highest_prev_bid > my_bid:
        # Try to outbid them, but don't exceed daily salary significantly
        my_bid = highest_prev_bid + 1

    # Adjust bid based on my HP (desperation)
    if my_status['hp'] <= 3:
        # Very desperate, bid very high
        my_bid = max(my_bid, DAILY_SALARY * 0.95) # 142.5
    if my_status['hp'] <= 1:
        # Extremely desperate, bid almost full salary
        my_bid = max(my_bid, DAILY_SALARY - 1) # 149

    # Adjust bid based on water scarcity
    # If supply is less than enough for 2 full requirements, competition is very high
    if day_context['supply'] < WATER_REQ * 2:
        my_bid = max(my_bid, DAILY_SALARY * 0.88) # 132

    # Ensure bid does not exceed daily salary (to prevent immediate debt)
    # and does not exceed current budget
    final_bid = min(my_status['budget'], my_bid, DAILY_SALARY)

    # Ensure bid is at least 0
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    remaining_days = EPISODE_DAYS - day_context['day'] + 1

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    base_bid = DAILY_SALARY * 0.5

    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] <= 7:
        base_bid = DAILY_SALARY * 0.65

    strong_opponent_bids_yesterday = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            if prev['bid'] > DAILY_SALARY * 0.3:
                strong_opponent_bids_yesterday.append(prev['bid'])

    if strong_opponent_bids_yesterday:
        max_prev_strong_bid = max(strong_opponent_bids_yesterday)
        avg_prev_strong_bid = sum(strong_opponent_bids_yesterday) / len(strong_opponent_bids_yesterday)

        num_possible_winners = math.floor(day_context['supply'] / WATER_REQ)

        if num_possible_winners < len(alive_opponents) + 1:
            if my_status['hp'] <= 4 or my_status['no_water_days'] > 0:
                base_bid = max(base_bid, max_prev_strong_bid + 5)
            else:
                base_bid = max(base_bid, avg_prev_strong_bid + 10)
        else:
            base_bid = max(base_bid, avg_prev_strong_bid + 2)
            if my_status['hp'] > 7 and my_status['budget'] > DAILY_SALARY * remaining_days * 0.5:
                 base_bid = min(base_bid, DAILY_SALARY * 0.7)

    final_bid = min(my_status['budget'], base_bid)

    if my_status['budget'] > 0 and final_bid <= 0:
        final_bid = min(my_status['budget'], 1.0)

    if my_status['budget'] < DAILY_SALARY * 0.2 and my_status['hp'] <= 3:
        final_bid = my_status['budget']

    final_bid = max(0.0, final_bid)

    return final_bid
"""
