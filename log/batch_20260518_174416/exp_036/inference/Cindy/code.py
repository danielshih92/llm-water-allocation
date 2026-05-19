# ============================================================
# Experiment: exp_036
# Agent: Cindy
# Source: exp_036
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
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    total_water_needed_by_opponents = sum([o['water_requirement'] for o in alive_opponents])
    total_water_demand = WATER_REQ + total_water_needed_by_opponents

    yesterday_bids = []
    for opp_data in alive_opponents:
        prev_trace = opp_data.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])
    
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0

    # --- Bidding Strategy ---

    # 1. Critical HP: Prioritize survival
    if my_hp <= 2:
        return min(my_budget, DAILY_SALARY * 0.95)

    # 2. Low HP: Still high priority
    if my_hp <= 4:
        # If supply is very tight (e.g., less than total demand + a buffer)
        if current_supply < total_water_demand + 5:
            return min(my_budget, DAILY_SALARY * 0.8)
        else:
            return min(my_budget, DAILY_SALARY * 0.7)

    # 3. Normal HP strategy
    base_bid = DAILY_SALARY * 0.4 # Default moderate bid

    # Adjust based on supply scarcity and competition
    if current_supply < total_water_demand + 5: # Supply is tight
        if highest_prev_bid > DAILY_SALARY * 0.5:
            base_bid = min(DAILY_SALARY * 0.7, highest_prev_bid + 5)
        else:
            base_bid = DAILY_SALARY * 0.55
    else: # Supply is relatively abundant
        if highest_prev_bid < DAILY_SALARY * 0.4:
            base_bid = max(DAILY_SALARY * 0.25, highest_prev_bid + 1)
        else:
            base_bid = DAILY_SALARY * 0.4
            if my_hp >= 8: # If HP is very good, be more conservative
                base_bid *= 0.85

    # Ensure bid doesn't exceed budget and meets a minimum competitive threshold
    final_bid = min(my_budget, max(base_bid, 15.0))

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

    # If no opponents are alive, bid minimal to get water
    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    # Calculate remaining days to manage budget
    # day_context['day'] is 1-indexed
    remaining_days = EPISODE_DAYS - day_context['day'] + 1
    
    # Calculate a sustainable budget per day to last the entire episode
    sustainable_daily_budget = my_status['budget'] / max(1, remaining_days)
    
    # Collect yesterday's bids from active opponents
    highest_prev_bid = 0.0
    for opp_id, opp in opponents_status.items():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and opp['alive']:
            if prev['bid'] > highest_prev_bid:
                highest_prev_bid = prev['bid']

    # Base bid: a moderate percentage of daily salary
    base_bid = DAILY_SALARY * 0.65 # Approximately 97.5

    # Adjust bid based on HP and opponent behavior
    my_current_hp = my_status['hp']

    # CRITICAL HP: Must get water to survive
    if my_current_hp <= 2:
        # Bid very aggressively, potentially exceeding sustainable_daily_budget
        bid = min(my_status['budget'], DAILY_SALARY * 0.95, sustainable_daily_budget * 1.5)
        # If there's a very high previous bid (Alex-like), try to beat it
        if highest_prev_bid >= DAILY_SALARY * 0.8: 
            bid = min(my_status['budget'], max(bid, highest_prev_bid + 5))
        return max(1.0, bid) # Ensure bid is at least 1.0

    # LOW HP: Urgent need for water
    if my_current_hp <= 5:
        # Bid aggressively, but try to stay within more reasonable limits than critical HP
        bid = min(my_status['budget'], DAILY_SALARY * 0.8, sustainable_daily_budget * 1.2)
        if highest_prev_bid >= DAILY_SALARY * 0.7:
            bid = min(my_status['budget'], max(bid, highest_prev_bid + 2))
        return max(1.0, bid)

    # STABLE HP: Strategic bidding to save budget while staying competitive
    if highest_prev_bid > 0:
        # If highest previous bid is very high (Alex-like)
        if highest_prev_bid >= DAILY_SALARY * 0.85: # e.g., > 127.5
            if my_current_hp > 7: # Good HP, can afford to be less aggressive to save budget
                bid = min(my_status['budget'], highest_prev_bid * 0.9, sustainable_daily_budget * 0.9)
            else: # Moderate HP, need to be more competitive
                bid = min(my_status['budget'], max(base_bid, highest_prev_bid + 1), sustainable_daily_budget * 1.05)
        # If highest previous bid is moderate
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # e.g., > 75
            bid = min(my_status['budget'], max(base_bid, highest_prev_bid + 1), sustainable_daily_budget * 1.0)
        # If highest previous bid is low (Bob/David-like)
        else:
            bid = min(my_status['budget'], max(base_bid, highest_prev_bid + 5), sustainable_daily_budget * 0.9)
    else:
        # No previous bids from active opponents (e.g., Day 1 or all opponents are new/passive)
        bid = min(my_status['budget'], base_bid, sustainable_daily_budget)
    
    # Ensure bid doesn't exceed current budget and is at least 1.0
    return max(1.0, min(bid, my_status['budget']))
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

    # If no opponents are alive, bid a minimal amount to conserve budget.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a competitive bid. Since supply is always < 2 * WATER_REQ,
    # only one player gets water, making it a winner-take-all scenario.
    # We must outbid the highest opponent.

    # Default strong competitive bid for Day 1 or if no previous bids are available.
    target_bid = DAILY_SALARY * 0.8 # 120.0

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If the highest previous bid was already competitive (e.g., >= 60% of salary),
        # bid slightly above it to win.
        if highest_prev_bid >= DAILY_SALARY * 0.6:
            target_bid = highest_prev_bid + 5.0 
        else:
            # If opponents bid very low yesterday, ensure we still bid a competitive amount
            # to not be caught off guard, but also try to win against their low bid.
            target_bid = max(target_bid, highest_prev_bid + 1.0)
            # Ensure a floor to prevent bidding too low in a competitive environment.
            target_bid = max(target_bid, DAILY_SALARY * 0.65)
    
    # Aggressive bidding if HP is critically low or water was missed previously.
    # HP <= 2 is a common critical threshold. 'no_water_days' indicates previous failure.
    if my_status['no_water_days'] >= 1 or my_status['hp'] <= 2:
        target_bid = DAILY_SALARY * 0.98 # Very aggressive (147.0)
        
        # On the very last day, if water is needed, bid all remaining budget to survive.
        if day_context['day'] == EPISODE_DAYS and my_status['no_water_days'] >= 1:
             target_bid = my_status['budget']
        elif my_status['hp'] <= 1: # Absolute emergency, bid just below full salary
            target_bid = DAILY_SALARY - 1.0 # 149.0

    # Ensure the bid does not exceed the current budget.
    final_bid = min(my_status['budget'], target_bid)

    # Ensure a minimum bid of 1.0 if budget allows and water is needed.
    if final_bid <= 0 and my_status['budget'] > 0 and my_status['hp'] > 0:
        final_bid = 1.0

    return final_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    # Bid factors based on my daily salary
    CRITICAL_HP_THRESHOLD = 2
    LOW_HP_THRESHOLD = 4

    CRITICAL_BID = DAILY_SALARY * 0.95 # 142.5
    HIGH_COMPETITION_BID_LOW_HP_FLOOR = DAILY_SALARY * 0.7 # 105
    HIGH_COMPETITION_BID_HIGH_HP = DAILY_SALARY * 0.45 # 67.5
    NORMAL_COMPETITION_BID_LOW_HP_FLOOR = DAILY_SALARY * 0.6 # 90
    NORMAL_COMPETITION_BID_HIGH_HP_FLOOR = DAILY_SALARY * 0.5 # 75
    DEFAULT_BID_CRITICAL_HP = DAILY_SALARY * 0.9 # 135
    DEFAULT_BID_NORMAL_HP = DAILY_SALARY * 0.65 # 97.5
    NO_OPPONENT_BID = DAILY_SALARY * 0.4 # 60

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid low to save budget
    if not alive_opponents:
        return min(my_status['budget'], NO_OPPONENT_BID)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    my_current_hp = my_status['hp']

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If my HP is critically low, bid very high to survive regardless of opponent bids
        if my_current_hp <= CRITICAL_HP_THRESHOLD:
            return min(my_status['budget'], CRITICAL_BID)
        
        # Check if opponents were bidding very high yesterday (e.g., above 85% of my daily salary)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_current_hp > LOW_HP_THRESHOLD: # Healthy enough to risk missing water, save budget
                return min(my_status['budget'], HIGH_COMPETITION_BID_HIGH_HP)
            else: # My HP is low, need to compete aggressively
                # Bid higher than highest_prev_bid, with a substantial floor
                return min(my_status['budget'], max(HIGH_COMPETITION_BID_LOW_HP_FLOOR, highest_prev_bid + 5))
        else: # Opponents were bidding moderately
            if my_current_hp <= LOW_HP_THRESHOLD: # My HP is low, need to compete
                # Bid slightly higher than highest_prev_bid, with a competitive floor
                return min(my_status['budget'], max(NORMAL_COMPETITION_BID_LOW_HP_FLOOR, highest_prev_bid + 2))
            else: # My HP is healthy
                # Bid competitively but not overly aggressive, with a moderate floor
                return min(my_status['budget'], max(NORMAL_COMPETITION_BID_HIGH_HP_FLOOR, highest_prev_bid + 1))
    else:
        # No yesterday's bids available (e.g., Day 1 of the meta-round)
        if my_current_hp <= CRITICAL_HP_THRESHOLD:
            return min(my_status['budget'], DEFAULT_BID_CRITICAL_HP)
        else:
            return min(my_status['budget'], DEFAULT_BID_NORMAL_HP)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        # If no opponents, bid low to save budget.
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # If there are yesterday bids, react to the highest pressure
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Check if the highest previous bid indicates high competition (above typical opponent max)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                # HP is good, but competition is very high, try to outbid but conserve if possible
                # Bid just above highest_prev_bid, but capped to avoid overspending unnecessarily.
                # This ensures competitiveness against very high bids.
                return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
            else:
                # HP is low, must win, bid very aggressively
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else:
            # Yesterday's highest bid was moderate, bid slightly above it to secure water
            # but don't overspend. This covers opponent's average and max bids.
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
    
    # Fallback if no yesterday bids or only low bids from yesterday
    # This part is also for the first day, or if all opponents are new or didn't bid yesterday.
    if my_status['hp'] <= 2:
        # Very low HP, must win
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    
    # Default bid when HP is good and no strong signal from yesterday
    # This is a competitive bid, around opponent's average.
    return min(my_status['budget'], DAILY_SALARY * 0.55)
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
    
    # If no active opponents, bid minimal to save budget, but still secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1) # Very low bid if no competition

    current_bid = DAILY_SALARY * 0.55 # Start with a solid base bid (around 82.5)

    # 1. Desperation Bidding (Highest Priority)
    if my_status['no_water_days'] > 0:
        current_bid = DAILY_SALARY * 0.95 # Bid very aggressively if already missed water
    elif my_status['hp'] <= 2: # Very low HP
        current_bid = DAILY_SALARY * 0.85 # Aggressive bid
    elif my_status['hp'] <= 4: # Low HP
        current_bid = max(current_bid, DAILY_SALARY * 0.75) # Increase bid

    # 2. Opponent Bidding Pressure (from yesterday's trace)
    yesterday_competitive_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and prev['bid'] > 0:
            # Filter out bids that are too high to be sustainable or too low (like David's 0)
            # Focus on bids from known strong players (Bob, Eric) or generally competitive bids
            if opp['agent_id'] in ["Bob", "Eric"]:
                # Strong opponents, their bids are very relevant
                yesterday_competitive_bids.append(prev['bid'])
            elif prev['bid'] > DAILY_SALARY * 0.2: # General competitive bid
                yesterday_competitive_bids.append(prev['bid'])

    if yesterday_competitive_bids:
        highest_prev_bid = max(yesterday_competitive_bids)
        # If the highest previous bid was significant, try to outbid it slightly
        if highest_prev_bid >= DAILY_SALARY * 0.6: # If opponents are bidding high
            current_bid = max(current_bid, highest_prev_bid + 5)
        elif highest_prev_bid > current_bid: # If opponents bid higher than my current plan, but not super high
            current_bid = max(current_bid, highest_prev_bid + 1)

    # 3. Supply Scarcity Adjustment
    supply = day_context['supply']
    # If supply is very low, it's highly competitive for even one player to get full water
    # My WATER_REQ is 13. If supply is 15, it's very tight.
    if supply < WATER_REQ * 1.2: # e.g., supply is 15-16. Highly competitive.
        current_bid = max(current_bid, DAILY_SALARY * 0.7)
    elif supply < WATER_REQ * 1.5 and len(alive_opponents) >= 2: # e.g., supply is 17-19. Tight if multiple active players.
        current_bid = max(current_bid, DAILY_SALARY * 0.65)
    
    # 4. End game strategy: If I have enough budget, ensure survival
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: # Last few days
        # If my budget is sufficient for high bids for the remaining days, be aggressive.
        # This is a heuristic; actual budget needed depends on future supply and bids.
        if my_status['budget'] > (DAILY_SALARY * 0.9 * remaining_days):
             current_bid = max(current_bid, DAILY_SALARY * 0.9)


    # Final constraints
    final_bid = min(current_bid, my_status['budget'])
    
    # Only bid above salary if very desperate (no_water_days > 0 or very low HP)
    if my_status['no_water_days'] == 0 and my_status['hp'] > 2:
        final_bid = min(final_bid, DAILY_SALARY * 1.0) # Cap at salary if not desperate

    # Ensure bid is non-negative
    final_bid = max(0.0, final_bid)

    return final_bid
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

    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    remaining_days = EPISODE_DAYS - current_day

    my_bid = DAILY_SALARY * 0.5

    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        my_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        my_bid = DAILY_SALARY * 0.8
    elif remaining_days <= 3 and my_status['hp'] <= 5:
        my_bid = DAILY_SALARY * 0.98
    elif remaining_days <= 2:
        my_bid = DAILY_SALARY * 0.75
    elif my_status['hp'] > 4 and remaining_days > 3:
        if num_alive_opponents > 0:
            my_bid = DAILY_SALARY * 0.65

    highest_prev_bid = 0
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev_trace['bid'])

    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 3:
                my_bid = max(my_bid, highest_prev_bid + 2)
            else:
                my_bid = max(my_bid, highest_prev_bid + 10)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            my_bid = max(my_bid, highest_prev_bid + 1)

    final_bid = min(my_status['budget'], my_bid)
    final_bid = max(0.0, final_bid)

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

    # If no opponents, bid conservatively to save budget, but ensure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine my base bid based on my health and no_water_days
    # This is the bid if no strong opponent pressure from yesterday
    if my_status['no_water_days'] > 0:
        # Very desperate, bid very high
        my_current_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 2:
        # Desperate, bid high
        my_current_bid = DAILY_SALARY * 0.9
    else:
        # Healthy, bid moderately to secure water
        my_current_bid = DAILY_SALARY * 0.65

    # Adjust bid based on opponent's highest previous bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Check if opponents are bidding very high (e.g., >= 85% of salary)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3 and my_status['no_water_days'] == 0:
                # If healthy and opponents are very aggressive, try to outbid slightly to get water
                my_current_bid = max(my_current_bid, highest_prev_bid + 1.0)
            else:
                # If desperate (low HP or missed water) and opponents are very aggressive, bid extremely high
                my_current_bid = max(my_current_bid, highest_prev_bid + 5.0) # Ensure I get it
        else:
            # If opponents are not extremely aggressive, but still present, slightly outbid them
            my_current_bid = max(my_current_bid, highest_prev_bid + 2.0)
    
    # Ensure the bid doesn't exceed current budget and is at least 1.0
    final_bid = min(my_status['budget'], my_current_bid)
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 

    bid_suggestion = DAILY_SALARY * 0.5

    if my_status['hp'] <= 3:
        bid_suggestion = DAILY_SALARY * 0.98
    elif my_status['hp'] <= 6:
        bid_suggestion = DAILY_SALARY * 0.8
    elif my_status['hp'] > 7:
        bid_suggestion = DAILY_SALARY * 0.45

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2, 50.0)

    previous_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            previous_bids.append(prev['bid'])

    if previous_bids:
        max_prev_bid = max(previous_bids)
        
        if max_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] <= 6:
                bid_suggestion = max(bid_suggestion, max_prev_bid + 5)
            else:
                if day_context['supply'] >= WATER_REQ:
                    if my_status['budget'] > max_prev_bid + 5:
                        bid_suggestion = max(bid_suggestion, max_prev_bid + 1)
        elif max_prev_bid >= DAILY_SALARY * 0.6:
            bid_suggestion = max(bid_suggestion, max_prev_bid + 1)
        else:
            if my_status['hp'] <= 6:
                bid_suggestion = max(bid_suggestion, max_prev_bid + 5)
            else:
                bid_suggestion = max(bid_suggestion, max_prev_bid + 1)

    if day_context['day'] >= EPISODE_DAYS - 2:
        if my_status['hp'] <= 6:
            bid_suggestion = max(bid_suggestion, DAILY_SALARY * 0.95)
        else:
            bid_suggestion = max(bid_suggestion, DAILY_SALARY * 0.7)

    final_bid = min(my_status['budget'], bid_suggestion)
    
    if my_status['hp'] <= 3:
        final_bid = min(final_bid, DAILY_SALARY * 1.05)
    else:
        final_bid = min(final_bid, DAILY_SALARY)

    final_bid = max(1.0, final_bid)

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)
    total_players_alive = num_alive_opponents + 1

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    my_bid = 0.0

    # 1. Determine base bid based on my health and game stage
    if my_status['hp'] <= 2: # Critical health, prioritize survival
        my_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low health, bid high
        my_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] <= 6 and day_context['day'] > int(EPISODE_DAYS * 0.6): # Mid-to-late game, moderate health, increase bid
        my_bid = DAILY_SALARY * 0.75
    else: # Healthy or early game, try to conserve budget
        my_bid = DAILY_SALARY * 0.55

    # 2. Adjust bid based on opponent's previous bids (if available)
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents were very aggressive
            my_bid = max(my_bid, highest_prev_bid * 1.03) # Bid slightly higher to win
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # Opponents were moderately aggressive
            my_bid = max(my_bid, avg_prev_bid * 1.1) # Bid above their average
        else: # Opponents were conservative
            my_bid = max(my_bid, highest_prev_bid + 5) # Bid just enough to win

    # 3. Apply supply pressure factor
    supply_units = int(day_context['supply'] // WATER_REQ)
    supply_pressure_factor = 1.0
    if supply_units < total_players_alive:
        # Not enough water for everyone, increase bid pressure
        supply_pressure_factor = 1.1
    elif supply_units >= total_players_alive + 1:
        # Plenty of water, reduce bid pressure
        supply_pressure_factor = 0.9

    my_bid *= supply_pressure_factor

    # 4. Final checks and limits
    my_bid = max(1.0, my_bid) # Minimum bid
    my_bid = min(my_status['budget'], my_bid) # Cannot exceed budget
    my_bid = min(DAILY_SALARY * 1.2, my_bid) # Cap bid to 120% of salary to prevent overpaying too much

    return my_bid
"""
