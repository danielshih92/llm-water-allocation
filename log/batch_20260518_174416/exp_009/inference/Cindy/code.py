# ============================================================
# Experiment: exp_009
# Agent: Cindy
# Source: exp_009
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If I'm the only one left, bid minimal to save budget.
    if num_alive_opponents == 0:
        return min(my_status['budget'], 1)

    # Determine how many water units of WATER_REQ can be supplied
    num_available_slots = int(day_context['supply'] // WATER_REQ)

    # Collect yesterday's bids from opponents
    yesterday_opponent_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_opponent_bids.append(prev_trace['bid'])

    # My desperation level
    is_desperate = my_status['no_water_days'] >= 1 or my_status['hp'] <= 2

    # Base bid
    my_bid = DAILY_SALARY * 0.4

    if is_desperate:
        # If desperate, bid very high to secure water
        my_bid = DAILY_SALARY * 0.95
        if my_status['no_water_days'] >= 2: # Even more desperate
            my_bid = DAILY_SALARY * 1.0

    # Adjust bid based on supply scarcity and opponent behavior
    # High competition: fewer slots than potential bidders (including myself)
    if num_available_slots < (num_alive_opponents + 1):
        if yesterday_opponent_bids:
            highest_prev_bid = max(yesterday_opponent_bids)
            # If desperate, ensure bid is high enough to beat previous high bids
            if is_desperate:
                my_bid = max(my_bid, highest_prev_bid + 5)
            else:
                # Not desperate, but supply is scarce, bid slightly above previous high
                my_bid = max(my_bid, highest_prev_bid + 1)
        else:
            # Scarce supply, no history, bid moderately high
            my_bid = max(my_bid, DAILY_SALARY * 0.6)
    else:
        # Abundant supply: enough slots for everyone
        if yesterday_opponent_bids:
            # If not desperate, try to bid just enough to get water, or save
            if not is_desperate:
                # Bid around average or slightly above minimum to save budget
                my_bid = min(my_bid, max(min(yesterday_opponent_bids) + 1, DAILY_SALARY * 0.2))
            else:
                # Still desperate, but supply is abundant, don't overspend too much
                my_bid = min(my_bid, max(DAILY_SALARY * 0.7, min(yesterday_opponent_bids) + 10))
        else:
            # Abundant supply, no history, bid low to save
            my_bid = min(my_bid, DAILY_SALARY * 0.25)

    # Ensure bid is within budget and non-negative
    final_bid = min(my_status['budget'], max(0, my_bid))

    # Ensure a minimum bid of 1 if budget allows and I need water
    if final_bid == 0 and my_status['budget'] > 0:
        final_bid = 1

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

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    # Initialize a base bid, a solid starting point given the scarcity
    base_bid = DAILY_SALARY * 0.65

    # --- Adjustments based on my status ---
    # Critical HP: Bid very high to ensure survival
    if my_hp <= 2:
        base_bid = DAILY_SALARY * 1.15 # Bid significantly above salary if desperate
    # Low HP: Bid aggressively
    elif my_hp <= 4:
        base_bid = DAILY_SALARY * 0.95
    
    # Consecutive days without water: Increase bid pressure significantly
    if my_no_water_days > 0:
        base_bid *= (1 + 0.15 * my_no_water_days) # Increase by 15% for each missed day

    # --- Adjustments based on game progression ---
    # Late game: Water becomes more critical for survival
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        base_bid *= 1.25
    elif current_day >= EPISODE_DAYS - 4: # Last 4 days
        base_bid *= 1.1

    # --- Adjustments based on opponent's previous bids ---
    yesterday_bids = []
    # Collect yesterday's bids from all opponents who have a trace
    for opp_id, opp in opponents_status.items():
        if opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None:
            yesterday_bids.append(opp['previous_trace']['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        # If the highest bid yesterday was already high, we need to outbid it
        if max_yesterday_bid > DAILY_SALARY * 0.9:
            base_bid = max(base_bid, max_yesterday_bid + 7.0) # Aggressively outbid
        elif max_yesterday_bid > DAILY_SALARY * 0.7:
            base_bid = max(base_bid, max_yesterday_bid + 3.0)
        else:
            base_bid = max(base_bid, max_yesterday_bid + 1.0) # Slightly higher

    # --- Specific handling for 'Eric' given his historical high bids ---
    eric_alive = False
    eric_previous_bid = 0.0
    for opp_id, opp in opponents_status.items():
        if opp_id == 'Eric' and opp['alive']:
            eric_alive = True
            if opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None:
                eric_previous_bid = opp['previous_trace']['bid']
            break

    if eric_alive:
        # If Eric is alive and bidding high, we must be very competitive
        if eric_previous_bid > DAILY_SALARY * 1.0: # Eric bid above salary
            base_bid = max(base_bid, eric_previous_bid + 10.0) # Outbid Eric strongly
        elif eric_previous_bid > DAILY_SALARY * 0.8:
            base_bid = max(base_bid, eric_previous_bid + 5.0)
        else:
            # Even if Eric's previous bid wasn't super high, maintain strong pressure
            base_bid = max(base_bid, DAILY_SALARY * 0.85)

    # Ensure the bid does not exceed current budget
    final_bid = min(my_budget, base_bid)

    # Ensure a reasonable minimum bid to stay in contention, unless budget is extremely low
    min_contention_bid = DAILY_SALARY * 0.35
    if my_budget < DAILY_SALARY * 0.5 and my_hp > 2: # Low budget, but not critical HP
        final_bid = min(final_bid, DAILY_SALARY * 0.5) # Conserve a bit
        final_bid = max(final_bid, min_contention_bid * 0.8)
    else:
        final_bid = max(final_bid, min_contention_bid)

    # Always return a positive bid, even if minimal
    return max(0.01, final_bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    my_current_budget = my_status['budget']
    my_current_hp = my_status['hp']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid logic, moderate by default
    bid = DAILY_SALARY * 0.55

    # Aggressive bidding if HP is low
    if my_current_hp <= 2:
        bid = DAILY_SALARY * 0.95 # Very aggressive
    elif my_current_hp <= 4:
        bid = DAILY_SALARY * 0.85 # Aggressive
    elif my_current_hp <= 6 and current_day > EPISODE_DAYS * 0.5: # Mid-late game, moderate HP, need to keep it up
        bid = DAILY_SALARY * 0.75

    # Adjust bid based on opponent's previous high bid
    if highest_prev_bid > 0:
        # If opponent bid very high (e.g., near their salary or mine)
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_current_hp > 6 and current_day < EPISODE_DAYS * 0.5: # If healthy and early game, can afford to lose a round to conserve budget
                bid = max(bid, DAILY_SALARY * 0.4) # Bid lower to conserve, accept temporary HP loss
            else: # Otherwise, I need to be competitive
                bid = max(bid, highest_prev_bid + 5) # Outbid them by a small margin
        # If opponent bid moderately high
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            bid = max(bid, highest_prev_bid + 2) # Slightly outbid
        # If opponent bid low
        else:
            bid = max(bid, DAILY_SALARY * 0.5) # Ensure a minimum competitive bid
    else: # If no previous bids from opponents (e.g., Day 1) or all were very low
        if my_current_hp <= 2:
            bid = DAILY_SALARY * 0.95
        elif my_current_hp <= 4:
            bid = DAILY_SALARY * 0.7
        else:
            bid = DAILY_SALARY * 0.55 # Default if no strong opponent bid history

    # Final checks
    final_bid = min(my_current_budget, bid)

    # Ensure bid is not too low if budget allows, to stay competitive
    if final_bid < DAILY_SALARY * 0.1 and my_current_budget > DAILY_SALARY * 0.1:
        final_bid = min(my_current_budget, DAILY_SALARY * 0.1)
    
    # If budget is very low, bid whatever is left to try and survive
    elif my_current_budget > 0 and final_bid < 1:
        final_bid = min(my_current_budget, 1.0)

    # If it's the last day and I have 0 HP, bid everything to survive
    if current_day == EPISODE_DAYS and my_current_hp == 0:
        final_bid = my_current_budget

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.75

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.8: # High pressure from opponents
            if my_status['hp'] > 4: # Relatively healthy, can risk saving a bit
                bid_amount = DAILY_SALARY * 0.65
            else: # HP is critical, must bid high to survive
                bid_amount = DAILY_SALARY * 0.95
        else: # Moderate pressure
            if my_status['hp'] <= 3: # HP is getting low, be more aggressive
                bid_amount = max(DAILY_SALARY * 0.85, highest_prev_bid + 10)
            else: # Healthy enough, try to be competitive but not overspend
                bid_amount = max(DAILY_SALARY * 0.65, highest_prev_bid + 5)
    else:
        # Day 1 or no previous bids available
        if my_status['hp'] <= 2: 
            bid_amount = DAILY_SALARY * 0.9
        else:
            bid_amount = base_bid

    remaining_days = EPISODE_DAYS - day_context['day']
    
    # Aggressive push in the final days if budget allows
    if remaining_days <= 2 and my_status['budget'] > DAILY_SALARY * 1.5:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.98)
    # Desperate bid if low on budget and HP in final days
    elif remaining_days <= 2 and my_status['budget'] < DAILY_SALARY * 0.5 and my_status['hp'] <= 2:
        bid_amount = my_status['budget'] # Bid everything
    # Conserve early if healthy
    elif day_context['day'] <= 3 and my_status['hp'] > 6:
        bid_amount = min(bid_amount, DAILY_SALARY * 0.7)

    final_bid = min(my_status['budget'], bid_amount)

    return max(0.01, final_bid)
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
    num_alive_opponents = len(alive_opponents)

    # If no opponents are alive, bid minimum to save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Get yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # If it's day 1 or no previous bids to react to, set an initial competitive bid
    if day_context['day'] == 1 or not yesterday_bids:
        if my_status['hp'] <= 2: # Critical HP, bid very high
            return min(my_status['budget'], DAILY_SALARY * 1.2) # 180
        elif my_status['hp'] <= 5: # Low HP, bid high
            return min(my_status['budget'], DAILY_SALARY * 0.9) # 135
        else: # Healthy HP, moderate-high bid
            return min(my_status['budget'], DAILY_SALARY * 0.8) # 120

    # If there are yesterday's bids, react to the highest one
    highest_prev_bid = max(yesterday_bids)
    my_current_bid = 0.0
    
    # HP-based urgency
    if my_status['hp'] <= 2: # Critical HP
        # Bid significantly above previous high to secure water
        my_current_bid = max(highest_prev_bid * 1.1, DAILY_SALARY * 1.3) # E.g., 110% of prev_bid or 195
    elif my_status['hp'] <= 4: # Low HP
        # Bid high enough to win, but slightly less critical than <=2 HP
        my_current_bid = max(highest_prev_bid * 1.05, DAILY_SALARY * 1.0) # E.g., 105% of prev_bid or 150
    else: # Healthy HP
        # If previous bid was very high, match/slightly exceed to stay competitive
        if highest_prev_bid >= DAILY_SALARY * 1.0: # If previous highest was >= 150
            my_current_bid = max(highest_prev_bid + 5, DAILY_SALARY * 0.9) # Small increment or 135
        # If previous bid was moderate, bid slightly above it
        else:
            my_current_bid = max(highest_prev_bid + 10, DAILY_SALARY * 0.85) # Increment or 127.5

    # Ensure bid is not negative and within budget
    return max(0.0, min(my_status['budget'], my_current_bid))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    bid = DAILY_SALARY * 0.6 

    if my_status['no_water_days'] >= 1:
        bid = DAILY_SALARY * 0.95
        if highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid + 10)
    elif my_status['hp'] <= 3:
        bid = DAILY_SALARY * 0.85
        if highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid + 5)
    else:
        if highest_prev_bid > 0:
            if highest_prev_bid >= DAILY_SALARY * 0.7:
                bid = max(bid, highest_prev_bid + 2)
            else:
                bid = max(bid, highest_prev_bid + 1)
        bid = max(bid, DAILY_SALARY * 0.55)

    if day_context['day'] >= 8:
        if my_status['budget'] > DAILY_SALARY * 2:
            bid = max(bid, DAILY_SALARY * 0.9)
        else:
            bid = max(bid, DAILY_SALARY * 0.75)

    final_bid = min(bid, my_status['budget'])

    if final_bid <= 0 and my_status['budget'] > 0 and (my_status['no_water_days'] >= 1 or my_status['hp'] <= 3):
        final_bid = 1

    return max(0, final_bid)
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

    # If no opponents are alive, bid minimum to get water
    if not alive_opponents:
        return min(my_status['budget'], 0.1)

    # Determine my desperation level
    # If HP is very low or I've missed water multiple days, bid extremely high
    if my_status['hp'] <= 1 or my_status['no_water_days'] >= 2:
        return min(my_status['budget'], DAILY_SALARY * 1.1) # Bid slightly above salary to ensure win

    # If HP is low or I missed water yesterday, bid very high
    if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1:
        return min(my_status['budget'], DAILY_SALARY * 0.95) # High bid, but not over salary

    # General bidding strategy
    yesterday_bids = []
    eric_prev_bid = 0
    eric_is_alive = False

    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
                if opp_id == "Eric":
                    eric_prev_bid = prev['bid']
                    eric_is_alive = True

    # Default bid if no previous bids or general case
    current_bid = DAILY_SALARY * 0.6 # Moderate starting point

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        current_bid = highest_prev_bid + 2.0 # Try to outbid the highest previous bidder

        # Aggressive adjustment if Eric is a known high bidder
        if eric_is_alive and eric_prev_bid > DAILY_SALARY * 0.8:
            current_bid = max(current_bid, eric_prev_bid + 5.0)
        elif eric_is_alive and eric_prev_bid > 0: # If Eric bid something, consider it
            current_bid = max(current_bid, eric_prev_bid + 2.0)

    # Consider the day and my HP to adjust aggression
    days_left = EPISODE_DAYS - day_context['day']
    
    if days_left <= 3: # Near the end, be more aggressive
        current_bid = max(current_bid, DAILY_SALARY * 0.8) # Ensure a strong bid
    elif my_status['hp'] > 5 and days_left > EPISODE_DAYS / 2: # Early/mid game, good HP, can save a bit
        current_bid = min(current_bid, DAILY_SALARY * 0.85) # Don't bid too high if not necessary
    else: # Default aggression for mid-game or moderate HP
        current_bid = min(current_bid, DAILY_SALARY * 0.95) # Cap at high but not over salary

    # Final bid must not exceed current budget
    final_bid = min(my_status['budget'], current_bid)

    # Ensure bid is at least a small positive value if I have budget
    if final_bid <= 0 and my_status['budget'] > 0:
        final_bid = 0.1
    elif final_bid < 0: # Should not happen, but for safety
        final_bid = 0.0

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
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    is_desperate = False
    if my_status['hp'] <= 2:
        is_desperate = True
    elif my_status['no_water_days'] >= 1 and day_context['day'] > 1:
        is_desperate = True
    elif day_context['day'] >= EPISODE_DAYS - 2 and my_status['hp'] < 5:
        is_desperate = True

    if is_desperate:
        desperation_factor = (EPISODE_DAYS - day_context['day'] + 1) * 2
        bid = DAILY_SALARY * 0.95 + desperation_factor
        return min(my_status['budget'], max(1, bid))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.6

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            bid = highest_prev_bid + 5
        else:
            bid = max(base_bid, highest_prev_bid + 2)
    else:
        bid = base_bid + (day_context['day'] * 2)

    return min(my_status['budget'], max(1, bid))
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

    # Default moderate bid
    bid_amount = DAILY_SALARY * 0.55

    # If no opponents, bid a safe amount to get water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # --- Collect yesterday's bids from alive opponents ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # --- Decision logic based on my status and opponent's previous actions ---

    # 1. Critical HP priority: Bid very high to survive
    if my_status['hp'] <= 2:
        bid_amount = DAILY_SALARY * 0.95
    # 2. Late game priority: Bid high to ensure survival for the end
    elif day_context['day'] >= EPISODE_DAYS - 1:
        bid_amount = DAILY_SALARY * 0.9
    # 3. Low HP priority (less critical than above):
    elif my_status['hp'] <= 4:
        bid_amount = DAILY_SALARY * 0.8
    # 4. React to very high opponent bids from yesterday
    elif highest_prev_bid >= DAILY_SALARY * 0.8:
        # If I'm also under pressure (low HP or late game), slightly exceed to win
        if my_status['hp'] <= 5 or day_context['day'] >= EPISODE_DAYS - 2:
            bid_amount = max(bid_amount, highest_prev_bid * 1.05)
        else:
            # Otherwise, match closely but conserve budget
            bid_amount = max(bid_amount, highest_prev_bid * 0.95)
    # 5. React to moderate opponent bids from yesterday
    elif highest_prev_bid >= DAILY_SALARY * 0.5:
        # Slightly exceed to stay competitive
        bid_amount = max(bid_amount, highest_prev_bid + 5)
    # 6. Default bid (if no strong conditions met)
    else:
        bid_amount = DAILY_SALARY * 0.55

    # Final adjustment based on budget and non-negative bid
    final_bid = min(my_status['budget'], bid_amount)
    final_bid = max(0.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid a minimal amount to secure water cheaply
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    else:
        # If no previous bids from alive opponents, use a baseline based on general competition
        highest_prev_bid = DAILY_SALARY * 0.6 # A reasonable baseline given strong opponents in meta-round

    # Calculate potential winners based on supply
    available_slots = int(day_context['supply'] // WATER_REQ)
    num_active_players = len(alive_opponents) + 1 # Me + alive opponents

    bid_amount = 0.0

    # Bidding strategy based on HP and competition
    if my_status['hp'] <= 3 or my_status['no_water_days'] > 0: # Desperate state: Low HP or no water days
        # Bid very aggressively
        if highest_prev_bid > 0:
            bid_amount = highest_prev_bid + (DAILY_SALARY * 0.15) # Bid significantly above previous highest
        else:
            bid_amount = DAILY_SALARY * 0.95 # Very high bid if no prior bids
    elif my_status['hp'] <= 6: # Medium HP, still need to be careful
        if num_active_players > available_slots: # High competition (not enough water for all who want it)
            if highest_prev_bid > 0:
                bid_amount = highest_prev_bid + (DAILY_SALARY * 0.08) # Slightly above
            else:
                bid_amount = DAILY_SALARY * 0.8
        else: # Enough water for all or more (lower competition)
            if highest_prev_bid > 0:
                bid_amount = max(highest_prev_bid, DAILY_SALARY * 0.7) # Match or higher baseline
            else:
                bid_amount = DAILY_SALARY * 0.7
    else: # Comfortable HP
        if num_active_players > available_slots: # High competition
            if highest_prev_bid > 0:
                bid_amount = highest_prev_bid + 1.0 # Just slightly above to win
            else:
                bid_amount = DAILY_SALARY * 0.65
        else: # Enough water for all or more
            if highest_prev_bid > 0:
                # Try to win cheaply, but still above a reasonable minimum
                bid_amount = max(highest_prev_bid * 0.9, DAILY_SALARY * 0.55)
            else:
                bid_amount = DAILY_SALARY * 0.55

    # Ensure bid is at least a minimal amount to participate
    bid_amount = max(1.0, bid_amount)

    # Ensure bid does not exceed budget
    return min(my_status['budget'], bid_amount)
"""
