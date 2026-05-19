# ============================================================
# Experiment: exp_016
# Agent: Cindy
# Source: exp_016
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
    
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_supply = day_context['supply']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Calculate total water demand (including myself)
    total_water_demand = WATER_REQ
    for opp in alive_opponents:
        total_water_demand += opp['water_requirement']

    # --- Bidding Strategy ---

    # 1. Survival mode: If I haven't gotten water recently, bid very high
    if my_no_water_days >= 1:
        return min(my_budget, DAILY_SALARY * 0.98) # Bid almost full salary to survive

    # 2. Collect opponent's previous bids
    yesterday_opponent_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_opponent_bids.append(prev_trace['bid'])

    # Determine a base bid
    base_bid = DAILY_SALARY * 0.5 # Moderate starting point

    if yesterday_opponent_bids:
        max_prev_opp_bid = max(yesterday_opponent_bids)
        avg_prev_opp_bid = sum(yesterday_opponent_bids) / len(yesterday_opponent_bids)

        # If highest previous bid was very high, we need to be competitive
        if max_prev_opp_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, max_prev_opp_bid + 1.0) # Bid slightly above highest to win

        # If average bid was moderate, aim to win by bidding slightly above average
        elif avg_prev_opp_bid > DAILY_SALARY * 0.5:
            base_bid = max(base_bid, avg_prev_opp_bid + 1.0) # Slightly above average

        # If bids were generally low, try to get water cheaply but still win
        else:
            base_bid = min(base_bid, avg_prev_opp_bid + 0.5) # Slightly above average, but keep it low
            
    # 3. Adjust based on supply vs. demand and number of competitors
    if current_supply < total_water_demand:
        # Supply is scarce, increase bid more aggressively
        # The more players and the lower the supply, the higher the competition
        competition_factor = (num_alive_opponents + 1) / 3.0 # Heuristic for competition
        scarcity_factor = (total_water_demand - current_supply) / (total_water_demand + 1e-6) # Normalize scarcity
        
        # Increase bid proportionally to scarcity and competition
        bid_increase = DAILY_SALARY * 0.2 * scarcity_factor * competition_factor
        base_bid = max(base_bid, base_bid + bid_increase)
    else:
        # Supply is sufficient, can try to be more conservative
        # If budget is good, try to save money
        if my_budget > DAILY_SALARY * 3 and my_no_water_days == 0:
            base_bid = min(base_bid, DAILY_SALARY * 0.4) # Try to get it cheaper
        else:
            base_bid = min(base_bid, DAILY_SALARY * 0.55) # Moderate bid if budget isn't super high

    # Final bid must not exceed budget and be at least 1.0
    final_bid = min(my_budget, base_bid)
    final_bid = max(1.0, final_bid)

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

    # Default bid: a strong baseline, inspired by successful high bidders in previous meta-rounds
    bid_amount = DAILY_SALARY * 0.75

    # Priority 1: My HP status
    # If HP is very low, bid aggressively
    if my_status['hp'] <= WATER_REQ: # I need water to survive the next day
        bid_amount = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 2 * WATER_REQ and my_status['no_water_days'] > 0: # Low HP and missed water yesterday
        bid_amount = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 3 * WATER_REQ: # Moderately low HP
        bid_amount = DAILY_SALARY * 0.85

    # Priority 2: Opponent's previous bids from yesterday's trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest opponent bid was high, I need to bid higher to compete
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            bid_amount = max(bid_amount, highest_prev_bid + 5.0)
        # If highest opponent bid was moderate, match or slightly exceed
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            bid_amount = max(bid_amount, highest_prev_bid + 2.0)
        # If highest opponent bid was low, I can try to win for less, but still be competitive
        else:
            bid_amount = max(bid_amount, highest_prev_bid + 10.0) # Ensure I'm not too low

    # Priority 3: End game strategy
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2:
        # If I need water to survive the remaining days
        if my_status['hp'] < WATER_REQ * remaining_days:
            bid_amount = max(bid_amount, my_status['budget']) # Bid everything if desperate
        else:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.9) # Be very aggressive

    # Ensure bid does not exceed current budget
    final_bid = min(bid_amount, my_status['budget'])
    # Ensure bid is at least 1.0 to participate
    final_bid = max(1.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to get water
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid
    base_bid = DAILY_SALARY * 0.6 # A general competitive bid

    # Adjust bid based on desperation (low HP or no water days)
    if my_hp <= 3 or my_no_water_days > 0:
        # Very desperate, bid high
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 6:
        # Somewhat desperate, bid higher
        base_bid = DAILY_SALARY * 0.85
    
    # Adjust bid based on game stage (end game)
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        base_bid = max(base_bid, DAILY_SALARY * 0.98) # Push hard to finish

    # React to opponent's previous bids if available
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If highest previous bid was very high, we might need to match or exceed
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            # If we are healthy, try to be competitive but not overspend
            if my_hp > 6:
                base_bid = max(base_bid, highest_prev_bid * 1.05)
            else: # Desperate, ensure we win
                base_bid = max(base_bid, highest_prev_bid + 5)
        elif avg_prev_bid < DAILY_SALARY * 0.4: # Opponents bidding low
            # If there's enough water, we can try to save
            if current_supply / (num_alive_opponents + 1) >= WATER_REQ:
                base_bid = min(base_bid, avg_prev_bid * 1.2)
            else: # Water is scarce, still need to be competitive
                base_bid = max(base_bid, DAILY_SALARY * 0.65)
        else: # Moderate bids from opponents
            # Try to bid slightly above average to win efficiently
            base_bid = max(base_bid, avg_prev_bid * 1.05)

    # Adjust based on supply relative to number of players
    # This is a rough estimate of how many water units each person might target
    potential_units_per_person = current_supply / (num_alive_opponents + 1)

    if potential_units_per_person >= WATER_REQ * 1.5: # Plenty of water for everyone
        # Try to save, bid a bit less if not desperate
        if my_hp > 5:
            base_bid *= 0.9
    elif potential_units_per_person < WATER_REQ: # Water is scarce
        # Be more aggressive
        base_bid *= 1.1
    
    # Ensure the bid is within budget and reasonable limits
    final_bid = min(my_budget, base_bid)
    final_bid = max(1.0, final_bid) # Bid at least 1

    # Round to 2 decimal places as bids are usually floats
    return round(final_bid, 2)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # --- 1. Determine a base bid --- 
    # Start with a bid that is competitive but not overly aggressive initially.
    # Opponents died quickly in the last meta-round, suggesting overbidding.
    # Let's try to outlast them by being slightly more conservative but still aiming to win.
    base_bid = DAILY_SALARY * 0.35 # ~52.5, competitive with Eric's average.

    # --- 2. Adjust based on my HP --- 
    if my_status['hp'] <= 2:  # Critical HP, must get water
        base_bid = DAILY_SALARY * 0.9 # 135
    elif my_status['hp'] <= 4: # Low HP, need water urgently
        base_bid = DAILY_SALARY * 0.7 # 105
    elif my_status['hp'] <= 6: # Medium-low HP
        base_bid = DAILY_SALARY * 0.5 # 75

    # --- 3. Adjust based on opponent behavior from previous_trace --- 
    max_prev_bid_from_desperate = 0

    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace:
            # If an opponent didn't get water yesterday, they might bid higher today.
            if prev_trace.get('status') == 'no_water':
                if prev_trace.get('bid') is not None:
                    max_prev_bid_from_desperate = max(max_prev_bid_from_desperate, prev_trace['bid'])
    
    # If there's a desperate opponent who bid high yesterday and didn't get water, react.
    if max_prev_bid_from_desperate > 0:
        # If my HP is critical or low, I need to outbid them.
        if my_status['hp'] <= 4:
            base_bid = max(base_bid, max_prev_bid_from_desperate + (DAILY_SALARY * 0.1)) # Bid slightly higher
        else: # If my HP is good, I can be slightly more cautious, but still competitive
            base_bid = max(base_bid, max_prev_bid_from_desperate + 1) # Just slightly higher

    # --- 4. Adjust based on competition level and supply --- 
    # How many agents can realistically get water?
    max_possible_winners = int(day_context['supply'] // WATER_REQ)
    if max_possible_winners == 0: 
        max_possible_winners = 1 # At least one can win as supply is >= WATER_REQ

    if num_alive_opponents > 0:
        if num_alive_opponents >= max_possible_winners: # High competition
            if my_status['hp'] > 6: # If healthy, I can afford to be slightly less aggressive
                base_bid = max(base_bid, DAILY_SALARY * 0.45) # 67.5
            else: # If HP is not great, be more aggressive
                base_bid = max(base_bid, DAILY_SALARY * 0.6) # 90
        else: # Fewer opponents than possible winners, less competition
            if my_status['hp'] > 6: # If healthy, can bid lower
                base_bid = min(base_bid, DAILY_SALARY * 0.3) # 45
            # If not healthy, still bid to secure water (base_bid is already higher)

    # If I'm the only one left, bid minimally
    if num_alive_opponents == 0:
        final_bid = DAILY_SALARY * 0.01 # 1.5, minimal bid to secure water
    else:
        final_bid = base_bid

    # --- 5. Final budget and non-negative checks --- 
    final_bid = min(my_status['budget'], final_bid)
    final_bid = max(0.0, final_bid) # Bid must be non-negative

    # Desperate last resort: if HP is 1 and I have budget, bid everything.
    if my_status['hp'] == 1 and my_status['budget'] > 0:
        final_bid = my_status['budget']

    return float(final_bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_BID_TO_WIN = 1.0 # A symbolic minimum, actual bid should be higher to be competitive

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimal to get water
    if num_alive_opponents == 0:
        return min(my_status['budget'], MIN_BID_TO_WIN)

    # Start with a base bid, typically around half salary
    base_bid = DAILY_SALARY * 0.5

    # Adjust base bid based on my HP and no_water_days
    if my_status['no_water_days'] > 0:
        base_bid = DAILY_SALARY * 1.2 # Very aggressive if I've missed water
    elif my_status['hp'] <= 3:
        base_bid = DAILY_SALARY * 1.0 # Aggressive if critical HP
    elif my_status['hp'] <= 6:
        base_bid = DAILY_SALARY * 0.8 # Moderate aggressive if low HP
    else:
        base_bid = DAILY_SALARY * 0.6 # Healthy HP, more conservative base

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # React to opponent bidding patterns
        if max_prev_bid >= DAILY_SALARY * 1.0: # Opponents are bidding extremely high
            if my_status['hp'] <= 5: # Critical HP, must win
                base_bid = max(base_bid, max_prev_bid + 10.0) # Outbid the highest
            else: # Healthy HP, but still need to compete
                base_bid = max(base_bid, avg_prev_bid * 1.1) # Bid slightly above average
        elif max_prev_bid <= DAILY_SALARY * 0.3: # Opponents are bidding very low
            base_bid = min(base_bid, DAILY_SALARY * 0.35) # Bid conservatively but ensure water
        else: # Moderate bidding from opponents
            base_bid = max(base_bid, avg_prev_bid * 1.05) # Slightly above average

    # Adjust bid based on supply scarcity
    total_water_units_needed = (num_alive_opponents + 1) * WATER_REQ
    if day_context['supply'] < total_water_units_needed: # Supply is scarce
        base_bid *= 1.15 # Increase bid to compete for limited water
    elif day_context['supply'] > total_water_units_needed * 1.5: # Supply is abundant
        base_bid *= 0.85 # Decrease bid as there's plenty of water

    # Final bid adjustments
    final_bid = max(base_bid, DAILY_SALARY * 0.1) # Ensure a minimum bid of 15.0

    # Cap bid at current budget
    final_bid = min(final_bid, my_status['budget'])

    # Ensure bid is not less than 1 (critical rule for valid bid)
    final_bid = max(final_bid, MIN_BID_TO_WIN)

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
    num_alive_opponents = len(alive_opponents)

    # If I'm the only one left, bid minimal to save budget.
    if num_alive_opponents == 0:
        return min(my_status['budget'], 1.0)

    remaining_days = EPISODE_DAYS - day_context['day']

    # --- Aggressive Bidding for Survival ---
    # If HP is critically low, bid very high to ensure water.
    if my_status['hp'] <= 2: # Very critical
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4: # Low HP, need water
        return min(my_status['budget'], DAILY_SALARY * 0.85)

    # --- Normal Bidding Strategy ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.6 # Default bid if no strong signals (90)

    bid = base_bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Try to outbid by a small margin, but don't go excessively high unless necessary
        target_bid = max(base_bid, highest_prev_bid + 5.0)

        if remaining_days > 0:
            avg_daily_budget_needed = my_status['budget'] / (remaining_days + 1)
            # If target_bid is much higher than average daily budget and my HP is good,
            # cap it slightly to conserve budget, but still aim to win.
            if my_status['hp'] > 5 and target_bid > avg_daily_budget_needed * 1.5:
                bid = min(target_bid, avg_daily_budget_needed * 1.5)
            else:
                bid = target_bid
        else: # Last day
            bid = target_bid
    else:
        # No previous bids from opponents (e.g., Day 1 or all prev bidders died)
        # Use the base bid, adjusted for remaining budget if it's tight on day 1
        if remaining_days > 0:
            avg_daily_budget_needed = my_status['budget'] / (remaining_days + 1)
            bid = min(base_bid, avg_daily_budget_needed * 1.2)
        else: # Last day
            bid = base_bid

    # Final check: Ensure bid doesn't exceed current budget
    return min(my_status['budget'], bid)
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
    EPISODE_DAYS = 10

    bid = DAILY_SALARY * 0.8

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        max_opp_bid_yesterday = max(yesterday_bids)
        if max_opp_bid_yesterday >= bid:
            bid = max_opp_bid_yesterday + 5

    if my_status['hp'] <= 3 or my_status['no_water_days'] > 0:
        bid = max(bid, DAILY_SALARY * 1.15)
        if my_status['hp'] == 1:
            bid = max(bid, DAILY_SALARY * 1.5)

    current_supply = day_context['supply']
    if current_supply <= WATER_REQ + 2:
        bid *= 1.2
    elif current_supply <= WATER_REQ + 5:
        bid *= 1.1
    elif current_supply >= MAX_SUPPLY - 5:
        bid *= 0.9

    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] < 10:
        bid = max(bid, DAILY_SALARY * 1.2)

    bid = min(bid, my_status['budget'])
    bid = max(bid, DAILY_SALARY * 0.4)
    
    bid = max(bid, 0.01)

    return bid
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
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_day = day_context['day']
    remaining_days = EPISODE_DAYS - current_day
    day_aggression_multiplier = 1.0
    if remaining_days <= 2:
        day_aggression_multiplier = 1.15
    elif remaining_days <= 4:
        day_aggression_multiplier = 1.08
    
    hp_adjustment = 0.0
    if my_status['hp'] <= 2:
        hp_adjustment = DAILY_SALARY * 0.2
    elif my_status['hp'] <= 4:
        hp_adjustment = DAILY_SALARY * 0.1

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        high_competition_threshold = DAILY_SALARY * 0.9 * day_aggression_multiplier

        if highest_prev_bid >= high_competition_threshold:
            if my_status['hp'] > 5:
                bid_amount = DAILY_SALARY * 0.7 * day_aggression_multiplier
                return min(my_status['budget'], bid_amount + hp_adjustment)
            else:
                bid_amount = max(highest_prev_bid + 5, DAILY_SALARY * 0.95)
                return min(my_status['budget'], (bid_amount + hp_adjustment) * day_aggression_multiplier)
        else:
            base_competitive_bid = DAILY_SALARY * 0.8
            bid_amount = max(base_competitive_bid, highest_prev_bid + 5)
            return min(my_status['budget'], (bid_amount + hp_adjustment) * day_aggression_multiplier)
    else:
        if my_status['hp'] <= 3:
            return min(my_status['budget'], (DAILY_SALARY * 0.95 + hp_adjustment) * day_aggression_multiplier)
        else:
            return min(my_status['budget'], (DAILY_SALARY * 0.8 + hp_adjustment) * day_aggression_multiplier)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
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
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # 1. Base bid calculation based on supply and my salary
    # Normalize supply: 0 for min_supply (15), 1 for max_supply (25)
    supply_normalized = (current_supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)

    # Base bid percentage of daily salary.
    # If supply is low (normalized ~0), bid higher (e.g., 95% of salary)
    # If supply is high (normalized ~1), bid lower (e.g., 50% of salary)
    # Linear interpolation: bid_percentage = 0.95 - (supply_normalized * (0.95 - 0.5))
    base_bid_percentage = 0.95 - (supply_normalized * 0.45)
    base_bid = DAILY_SALARY * base_bid_percentage

    # 2. Survival adjustment: Prioritize getting water if HP is low
    if my_hp <= 1: # Critical - must get water to survive
        # Bid very aggressively, potentially above daily salary if budget allows
        base_bid = max(base_bid, DAILY_SALARY * 1.1) # Up to 110% of salary
    elif my_hp <= 2: # High priority
        base_bid = max(base_bid, DAILY_SALARY * 0.95)
    elif my_no_water_days >= 1: # Missed water yesterday, try to recover
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    # 3. Opponent analysis from yesterday's trace
    highest_prev_successful_bid = 0.0
    
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev_trace = opp_data.get('previous_trace', {})
            # Ensure trace is for yesterday and not empty
            if prev_trace and prev_trace.get('day') == current_day - 1:
                opp_bid = prev_trace.get('bid')
                if opp_bid is not None:
                    # If opponent received water yesterday, their bid was successful
                    if prev_trace.get('status') == 'Water received':
                        highest_prev_successful_bid = max(highest_prev_successful_bid, opp_bid)

    # If there was a high successful bid yesterday, adjust my bid to be competitive
    if highest_prev_successful_bid > 0 and num_alive_opponents > 0:
        # If my current base bid is lower than yesterday's highest successful bid, consider raising it
        # especially if I need water or supply is low
        if base_bid < highest_prev_successful_bid * 1.05 and (my_hp <= 3 or supply_normalized < 0.5):
            base_bid = max(base_bid, highest_prev_successful_bid * 1.05)
        # If my HP is good and supply is high, maybe don't chase yesterday's high bid too much
        elif my_hp > 3 and supply_normalized > 0.7:
             base_bid = min(base_bid, highest_prev_successful_bid * 0.9) # Try to get it cheaper

    # 4. Special cases
    if num_alive_opponents == 0:
        # If no opponents, bid minimally to save budget
        return min(my_budget, WATER_REQ * 1.0) # Bid 1 per unit of water

    if current_day == EPISODE_DAYS:
        # Last day, bid all remaining budget if I need water to survive or for final score
        if my_no_water_days > 0 or my_hp <= 2:
            return my_budget
        else:
            # If not desperate, but still want to participate, bid a reasonable amount
            return min(my_budget, DAILY_SALARY * 0.6) # A moderate bid to try and win

    # Final bid cannot exceed budget
    final_bid = min(my_budget, base_bid)

    # Ensure a minimal bid if I need water and have budget, to avoid bidding 0
    if final_bid < WATER_REQ * 1.0 and my_budget >= WATER_REQ * 1.0 and my_hp > 0:
        final_bid = WATER_REQ * 1.0
    elif final_bid <= 0 and my_hp > 0: # If calculated bid is zero or negative but I need water
        final_bid = min(my_budget, WATER_REQ * 0.5) # Try a very small bid if budget allows
        if final_bid <= 0: # Still zero, means budget is too low
            return 0.0 # Cannot bid

    return round(final_bid, 2)
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

    # Default bid (starting point, will be adjusted upwards by conditions)
    bid_amount = DAILY_SALARY * 0.55

    # Priority 1: Survival (Low HP or No Water Days)
    if my_hp <= 2 or my_no_water_days > 0:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.95) # Bid very aggressively
    elif my_hp <= 4:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.8) # Bid aggressively

    # Priority 2: Opponent Reaction (based on yesterday's bids)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents bid very high (e.g., >= 80% of salary)
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_hp > 4: # If relatively healthy, try to be slightly less aggressive but competitive
                if current_supply <= WATER_REQ + 2: # Very scarce supply, need to be aggressive
                    bid_amount = max(bid_amount, highest_prev_bid + 5)
                else:
                    bid_amount = max(bid_amount, highest_prev_bid * 0.95) # Try to get it slightly cheaper
            else: # If my HP is low, I must outbid
                bid_amount = max(bid_amount, highest_prev_bid + 5)
        # If opponents bid moderately (e.g., >= 50% of salary)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            bid_amount = max(bid_amount, highest_prev_bid + 2) # Slightly outbid
        # If opponents bid low, the initial bid_amount (0.55 * DAILY_SALARY) should be competitive.
    
    # Priority 3: Late Game Desperation
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        bid_amount = max(bid_amount, DAILY_SALARY * 0.9) # Ensure high bid late game
    elif current_day >= EPISODE_DAYS - 4: # Last 4 days
        bid_amount = max(bid_amount, DAILY_SALARY * 0.7) # Higher bid mid-late game

    # Priority 4: Supply Scarcity
    # If supply is low, competition is higher. Supply range: [15, 25]
    if current_supply <= WATER_REQ + 2: # Very scarce supply (e.g., 15)
        bid_amount = max(bid_amount, DAILY_SALARY * 0.85)
    elif current_supply <= WATER_REQ + 5: # Moderately scarce (e.g., 16-18)
        bid_amount = max(bid_amount, DAILY_SALARY * 0.7)

    # Final Bid Adjustment
    final_bid = min(my_budget, bid_amount)

    # If budget is positive but calculated bid is zero or negative, bid a minimal amount
    if final_bid <= 0 and my_budget > 0:
        final_bid = 1.0
    
    # If no opponents, bid very low to save budget
    if not alive_opponents:
        final_bid = min(my_budget, DAILY_SALARY * 0.1)

    return final_bid
"""
