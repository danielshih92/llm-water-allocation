# ============================================================
# Experiment: exp_110
# Agent: Cindy
# Source: exp_110
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

    # If no opponents, bid a minimal amount to secure water
    if num_alive_opponents == 0:
        return min(my_status['budget'], 1)

    # Critical HP: Bid aggressively to survive
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # Healthy HP: Adjust bid based on supply scarcity
    current_supply = day_context['supply']
    bid = DAILY_SALARY * 0.5 # Default moderate bid

    if current_supply <= WATER_REQ: # Only enough for one or less
        bid = DAILY_SALARY * 0.8
    elif current_supply <= WATER_REQ * 1.5: # Enough for one, tight for a second
        bid = DAILY_SALARY * 0.65
    else: # More abundant supply
        bid = DAILY_SALARY * 0.55

    # Ensure bid does not exceed budget
    return min(my_status['budget'], bid)
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
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to secure water
    if num_alive_opponents == 0:
        # Bid enough to cover water_req if budget allows, otherwise minimal
        return min(my_status['budget'], WATER_REQ * 1.1 if my_status['budget'] >= WATER_REQ else 1.0)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine my base bid
    base_bid = DAILY_SALARY * 0.55 # A moderate default bid

    # Check for my desperation
    is_my_hp_low = my_status['hp'] <= 3 or my_status['no_water_days'] > 0
    is_end_game = day_context['day'] >= EPISODE_DAYS - 2 # Last 2 days are critical

    # Adjust base bid if I'm desperate or it's end game
    if is_my_hp_low:
        if is_end_game:
            base_bid = DAILY_SALARY * 0.99 # Extremely aggressive if desperate and end game
        else:
            base_bid = DAILY_SALARY * 0.95 # Very aggressive if desperate
    elif is_end_game: # Not desperate but end game, be more competitive
        base_bid = DAILY_SALARY * 0.8

    # React to yesterday's highest bid if available
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If yesterday's highest bid was very high
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 5: # If relatively healthy, can risk saving money
                base_bid = min(base_bid, DAILY_SALARY * 0.4) # Bid lower, might lose water
            else: # Not very healthy, need water
                base_bid = max(base_bid, highest_prev_bid + 2.0) # Ensure to outbid
        # If yesterday's highest bid was moderate
        else:
            base_bid = max(base_bid, highest_prev_bid + 1.5) # Slightly exceed

    # Consider supply: if supply is very tight, increase bid
    # Supply range is [15, 25]. My requirement is 13.
    # If supply is 15-18, it's very competitive for one player.
    if day_context['supply'] <= WATER_REQ + 5: # Supply is tight
        base_bid = max(base_bid, DAILY_SALARY * 0.65) # Ensure a minimum competitive bid

    # Final bid must not exceed budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure the bid is at least enough to cover water requirement if budget allows
    # and not 0, unless budget is truly 0
    if my_status['budget'] > 0:
        final_bid = max(final_bid, WATER_REQ * 1.1 if my_status['budget'] >= WATER_REQ else 1.0)
    else:
        final_bid = 0.0 # If budget is 0, bid 0

    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no active opponents, bid low to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Decision logic based on yesterday's highest pressure
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents are bidding very high (e.g., >= 85% of their daily salary)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # Healthy, can afford to save budget
                bid_value = DAILY_SALARY * 0.3 # Bid lower (45)
            else: # Not healthy, need to compete aggressively
                bid_value = DAILY_SALARY * 0.95 # Bid high (142.5)
        else: # Opponents are bidding moderately or low
            # Try to outbid slightly, but ensure it's at least a reasonable baseline
            # Using 5.0 as a small margin to outbid, adjusted for higher salaries
            bid_value = max(DAILY_SALARY * 0.5, highest_prev_bid + 5.0) # Baseline 75 or (prev_bid + 5)
    else: # No previous bids from active opponents (e.g., Day 1 or all previous bidders died)
        if my_status['hp'] <= 2: # Very low HP, desperate
            bid_value = DAILY_SALARY * 0.9 # Bid high (135)
        else: # Standard bid if no previous opponent data
            bid_value = DAILY_SALARY * 0.55 # Moderate bid (82.5)

    # Ensure bid does not exceed available budget
    final_bid = min(my_status['budget'], bid_value)
    
    # Ensure bid is at least 1.0 to always attempt to get water if budget allows
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    base_bid = DAILY_SALARY * 0.5 

    # Adjust based on my HP
    if my_status['hp'] <= 0: 
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 2: 
        base_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] <= 4: 
        base_bid = DAILY_SALARY * 0.65

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    highest_opponent_bid_yesterday = 0.0
    strong_opponents_yesterday_bids = []

    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                if opp_id in ["Alex", "Eric"]:
                    strong_opponents_yesterday_bids.append(prev['bid'])
                highest_opponent_bid_yesterday = max(highest_opponent_bid_yesterday, prev['bid'])

    # React to strong opponents' previous bids
    if strong_opponents_yesterday_bids:
        avg_strong_bid = sum(strong_opponents_yesterday_bids) / len(strong_opponents_yesterday_bids)
        if avg_strong_bid > DAILY_SALARY * 0.7: 
            base_bid = max(base_bid, avg_strong_bid * 1.05) 
        elif avg_strong_bid > DAILY_SALARY * 0.5:
            base_bid = max(base_bid, avg_strong_bid * 1.02)

    # If general highest bid was very high, react
    if highest_opponent_bid_yesterday > DAILY_SALARY * 0.75:
        base_bid = max(base_bid, highest_opponent_bid_yesterday + 5.0)

    # Adjust based on supply
    if day_context['supply'] <= MIN_SUPPLY + 2: 
        base_bid *= 1.2
    elif day_context['supply'] <= MIN_SUPPLY + 5: 
        base_bid *= 1.1

    # Adjust for end game (last few days)
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: 
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif remaining_days <= 4: 
        base_bid = max(base_bid, DAILY_SALARY * 0.75)

    final_bid = min(my_status['budget'], base_bid)
    final_bid = max(1.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQ = 13
    MY_DAILY_SALARY = 150
    
    current_day = day_context['day']
    current_supply = day_context['supply']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Base bid: a fraction of daily salary
    # Start with a moderate bid, aiming for survival and budget conservation
    base_bid = MY_DAILY_SALARY * 0.6
    
    # --- Adjust bid based on my HP and recent water status ---
    if my_status['hp'] <= 2: # Critical HP: Must get water
        base_bid = MY_DAILY_SALARY * 0.98 # Bid very high
    elif my_status['no_water_days'] > 0: # Missed water yesterday: High urgency
        base_bid = MY_DAILY_SALARY * 0.90
    elif my_status['hp'] <= 4: # Low HP: High urgency
        base_bid = MY_DAILY_SALARY * 0.85
    elif my_status['hp'] <= 6: # Medium-low HP
        base_bid = MY_DAILY_SALARY * 0.75
    
    # --- Adjust bid based on competition and supply ---
    num_active_players = len(alive_opponents) + 1 # Including myself
    
    # Estimate how many players can potentially get their full water requirement
    # For simplicity, let's consider how many *my* requirement slots fit into supply
    num_my_water_req_slots = int(current_supply // MY_WATER_REQ)
    
    competition_premium = 0 # Additional bid amount due to competition
    
    if num_active_players > num_my_water_req_slots:
        # High competition: More players than available 'slots' for my water_req
        competition_premium = MY_DAILY_SALARY * 0.2
    elif num_active_players == num_my_water_req_slots and num_active_players > 1:
        # Moderate competition: Exactly enough slots, but still competitive
        competition_premium = MY_DAILY_SALARY * 0.1
    elif num_active_players < num_my_water_req_slots and num_active_players > 0:
        # Low competition: More slots than players, can bid lower
        competition_premium = MY_DAILY_SALARY * -0.1 # Reduce bid
    
    final_bid = base_bid + competition_premium
    
    # --- Adjust bid based on opponents' previous bids ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])
            
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        # If opponents bid high, ensure we can outbid them if necessary
        # Add a small buffer to max_yesterday_bid to increase chances of winning
        if max_yesterday_bid >= MY_DAILY_SALARY * 0.7: # If opponent bid was high
            final_bid = max(final_bid, max_yesterday_bid + 5)
        elif max_yesterday_bid >= MY_DAILY_SALARY * 0.5: # If opponent bid was moderate
            final_bid = max(final_bid, max_yesterday_bid + 2)
        else: # If opponent bid was low, still try to be competitive
            final_bid = max(final_bid, max_yesterday_bid * 1.1)

    # Ensure bid is not too low, even in low competition, to avoid being outbid by a trivial amount
    final_bid = max(final_bid, MY_DAILY_SALARY * 0.25)
    
    # Final constraint: Cannot bid more than current budget
    return min(my_status['budget'], final_bid)
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
        return min(my_status['budget'], 1.0)

    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    day_factor = day_context['day'] / EPISODE_DAYS
    base_bid = DAILY_SALARY * (0.4 + 0.5 * day_factor)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.80:
            if my_status['hp'] > 4:
                return min(my_status['budget'], max(base_bid, highest_prev_bid + 1.0))
            else:
                return min(my_status['budget'], max(DAILY_SALARY * 0.9, highest_prev_bid + 1.0))
        else:
            return min(my_status['budget'], max(base_bid, highest_prev_bid + 1.0))
    
    return min(my_status['budget'], base_bid)
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
    num_alive_opponents = len(alive_opponents)

    # Rule 1: No opponents left, bid minimally to save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1) # Bid very low if no competition

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine the highest bid from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Base bid strategy: Aim to outbid the highest previous bid
    bid_amount = highest_prev_bid + 1.0 

    # If no previous bids or they were very low, establish a reasonable base
    if bid_amount < DAILY_SALARY * 0.4:
        bid_amount = DAILY_SALARY * 0.4

    # Adjust bid based on my HP and no_water_days (survival priority)
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0: # Critical HP or missed water
        bid_amount = max(bid_amount, DAILY_SALARY * 0.95) # Bid very aggressively
    elif my_status['hp'] <= 4: # Low HP
        bid_amount = max(bid_amount, DAILY_SALARY * 0.8) # Bid aggressively
    
    # Adjust bid for late game pressure (ensure strong finish)
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days
        if my_status['hp'] > 0: 
            bid_amount = max(bid_amount, DAILY_SALARY * 0.85) # Be very aggressive
        if my_status['hp'] <= 2: # If desperate in late game
            bid_amount = DAILY_SALARY * 0.99 # Max out to survive

    # Ensure bid does not exceed my current budget and is not negative
    final_bid = min(my_status['budget'], bid_amount)
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
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid calculation
    current_bid = DAILY_SALARY * 0.5 # Default moderate bid

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP, bid very aggressively
        current_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP, bid aggressively
        current_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] >= 8: # Healthy HP, can be less aggressive if not much competition
        current_bid = DAILY_SALARY * 0.45 # Default for healthy, will be adjusted

    # Adjust bid based on supply scarcity and number of competitors
    supply = day_context['supply']
    available_slots = int(supply / WATER_REQ)
    num_competitors = len(alive_opponents) + 1

    if num_competitors > available_slots: # High competition for water
        # Increase bid, especially if HP is not great
        if my_status['hp'] <= 4:
            current_bid = max(current_bid, DAILY_SALARY * 0.9) # Ensure high bid
        else:
            current_bid = max(current_bid, DAILY_SALARY * 0.7) # Be competitive
    else: # Enough water for everyone (or more than enough slots)
        if my_status['hp'] >= 8: # If healthy and low competition, try to save money
            current_bid = min(current_bid, DAILY_SALARY * 0.4) # Bid lower to save
        else: # Still need water, but less pressure
            current_bid = min(current_bid, DAILY_SALARY * 0.6) # Moderate bid to secure


    # Adjust bid based on opponent's previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents bid very high, react strongly
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            current_bid = max(current_bid, highest_prev_bid + 5) # Try to outbid
        # If opponents bid moderately high
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            current_bid = max(current_bid, highest_prev_bid + 2)
        # If opponents bid low, and I'm healthy, try to save
        elif my_status['hp'] >= 8:
            current_bid = min(current_bid, highest_prev_bid + 1)
        else: # Opponents bid low, but I need water
            current_bid = max(current_bid, highest_prev_bid + 1)

    # End game pressure: last 2 days
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2:
        if my_status['hp'] <= 4: # Critical HP at end game
            current_bid = max(current_bid, DAILY_SALARY * 0.98) # Bid almost everything
        else: # Still want to finish strong
            current_bid = max(current_bid, DAILY_SALARY * 0.8)

    # Final bid must not exceed budget
    return min(my_status['budget'], current_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    # Base bid strategy
    base_bid = DAILY_SALARY * 0.8 # Start with 120

    # Adjust for my HP
    if my_status['hp'] <= 2: # Critical HP, must win
        base_bid = DAILY_SALARY * 1.25 # 187.5
    elif my_status['hp'] <= 5: # Low HP
        base_bid = DAILY_SALARY * 1.0 # 150
    elif my_status['hp'] >= 8: # Good HP, can save
        base_bid = DAILY_SALARY * 0.7 # 105
    # For HP 6-7, base_bid remains at the initial 0.8 * DAILY_SALARY (120)

    # Adjust for supply
    # If supply is low (15), only one agent can get water. Competition is high.
    # If supply is high (25), two agents can potentially get water. Competition might be lower.
    if day_context['supply'] <= WATER_REQ: # Only one winner possible
        base_bid *= 1.15 # Increase bid
    elif day_context['supply'] >= WATER_REQ * 2: # Two winners possible
        base_bid *= 0.85 # Decrease bid

    # Adjust for day number (late game pressure)
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days
        base_bid *= 1.15 # Increase bid due to urgency
    elif day_context['day'] <= 2: # Early game, be a bit more cautious but still competitive
        base_bid *= 0.95


    # Opponent analysis from previous_trace
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest bid was very high, it suggests aggressive opponents.
        if highest_prev_bid > base_bid * 1.05: # Opponents were very aggressive
            if my_status['hp'] <= 5: # Low to critical HP, must match/exceed
                base_bid = max(base_bid, highest_prev_bid + 5)
            else: # Sufficient HP, be competitive but not overly aggressive
                base_bid = max(base_bid, highest_prev_bid * 0.95) # Try to be just below, or match
        elif highest_prev_bid < base_bid * 0.8: # Opponents were less aggressive than my current base
            base_bid = min(base_bid, highest_prev_bid + 10) # Try to get it cheaper, but still win

    # Ensure bid is within budget and positive
    final_bid = min(my_status['budget'], max(0.0, base_bid))

    # Critical override: If HP is 1, I MUST get water. Bid almost all budget.
    if my_status['hp'] == 1:
        final_bid = my_status['budget'] * 0.95 # Leave a tiny bit for margin

    return final_bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # Total days in the episode

    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents are alive, bid just enough to cover my water requirement, or save budget.
    if not alive_opponents:
        # If I'm the only one left, bid low, but ensure I get water if my HP is low.
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.5) # Still bid something to ensure water
        return min(my_status['budget'], DAILY_SALARY * 0.2) # Very low bid if not critical
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid strategy
    base_bid = DAILY_SALARY * 0.5 # Default moderate bid
    
    # Survival strategy: If HP is very low, bid aggressively
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # Dynamic bidding based on yesterday's competition
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)
        
        # If competition was very high yesterday
        if max_prev_bid >= DAILY_SALARY * 0.85: # If highest bid was 85% or more of daily salary
            # If my HP is still good, try to conserve budget, hoping others exhaust.
            if my_status['hp'] > 4:
                base_bid = DAILY_SALARY * 0.6 # Slightly lower, but still competitive
            else: # If HP is getting lower, I need water more urgently
                base_bid = max(DAILY_SALARY * 0.8, max_prev_bid + 5) # Bid high to secure water
        else: # Moderate competition yesterday
            # Bid slightly above average or max to outcompete
            base_bid = max(DAILY_SALARY * 0.7, avg_prev_bid + 5)
            
            # Adjust bid based on remaining days and current HP
            remaining_days = EPISODE_DAYS - current_day
            if remaining_days <= 3 and my_status['hp'] > 0: # End game push
                base_bid = max(base_bid, DAILY_SALARY * 0.8) # Be more aggressive towards the end

    else: # No previous bids (e.g., Day 1, or all previous opponents died)
        # On Day 1, or if no info, bid moderately high due to limited supply.
        base_bid = DAILY_SALARY * 0.75
        
        # If supply is very low compared to requirements, be more aggressive
        # Total water needed by alive players (approx, if everyone needs WATER_REQ)
        num_alive_players = len(alive_opponents) + 1 # Me + opponents
        if current_supply < num_alive_players * WATER_REQ * 0.5: # If supply is less than half of total need
            base_bid = max(base_bid, DAILY_SALARY * 0.85)

    # Ensure bid doesn't exceed current budget
    final_bid = min(my_status['budget'], base_bid)
    
    # Ensure bid is at least 0
    return max(0.0, final_bid)
"""
