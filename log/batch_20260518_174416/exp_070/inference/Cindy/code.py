# ============================================================
# Experiment: exp_070
# Agent: Cindy
# Source: exp_070
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From Current Meta-Round State

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_players = len(alive_opponents) + 1 # Myself + opponents

    current_supply = day_context['supply']
    current_day = day_context['day']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    # --- Determine initial base bid based on my health ---
    if my_no_water_days >= 2: # Critical: Must get water
        bid_multiplier = 0.95
    elif my_no_water_days == 1: # Stressed: Need water
        bid_multiplier = 0.7
    else: # Healthy: Can afford to be strategic
        bid_multiplier = 0.4 # Default moderate bid to save budget

    base_bid = DAILY_SALARY * bid_multiplier

    # --- Adjust bid based on supply scarcity ---
    total_water_needed_approx = WATER_REQ * num_alive_players
    if current_supply < total_water_needed_approx:
        # If supply is very low (e.g., only enough for one player)
        if current_supply < WATER_REQ:
            base_bid = max(base_bid, DAILY_SALARY * 0.85) # Bid very high to secure
        else: # Supply is somewhat scarce, but maybe enough for some
            base_bid = max(base_bid, DAILY_SALARY * 0.65) # Bid higher to compete
    else: # Supply is abundant, can bid lower if healthy
        if my_no_water_days == 0:
            base_bid = min(base_bid, DAILY_SALARY * 0.3) # Save money if healthy and abundant supply

    # --- React to opponent's previous bids ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were bidding high, react
        if highest_prev_bid >= DAILY_SALARY * 0.7: # High bid threshold
            base_bid = max(base_bid, highest_prev_bid + 5) # Try to outbid
        elif highest_prev_bid >= DAILY_SALARY * 0.4: # Moderate bid threshold
            base_bid = max(base_bid, highest_prev_bid + 2) # Try to outbid slightly

    # --- Final bid adjustments ---
    final_bid = min(my_budget, base_bid) # Cannot bid more than budget
    final_bid = max(final_bid, DAILY_SALARY * 0.1) # Ensure a minimum bid (e.g., 15)

    # Late-game aggressive push if in a good position
    if current_day >= EPISODE_DAYS - 2: # Last 3 days (e.g., day 8, 9, 10 if EPISODE_DAYS=10)
        if my_no_water_days == 0 and my_budget > DAILY_SALARY * 2: # Healthy and good budget
            final_bid = max(final_bid, DAILY_SALARY * 0.8) # Push for win

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
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_players = len(alive_opponents) + 1

    # Determine potential number of winners based on current supply
    potential_winners = int(current_supply // WATER_REQ)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # Default bid if no strong signals or for initial rounds
    base_bid = DAILY_SALARY * 0.65

    # If I'm in critical condition (low HP or consecutive no water days)
    if my_hp <= 2 or my_no_water_days >= 1:
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 5: # Low but not critical
        base_bid = DAILY_SALARY * 0.85

    # Adjust based on remaining days - become more aggressive towards the end
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last 2 days
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif remaining_days <= 4: # Mid-late game
        base_bid = max(base_bid, DAILY_SALARY * 0.75)

    # Adjust based on opponent's previous bids and supply scarcity
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        if potential_winners < num_alive_players: # Supply is scarce
            # If others bid high and supply is tight, I must bid higher
            if highest_prev_bid >= DAILY_SALARY * 0.7:
                base_bid = max(base_bid, highest_prev_bid + 5) # Try to outbid the highest
            else:
                base_bid = max(base_bid, avg_prev_bid * 1.1) # Slightly more aggressive than average
        else: # Supply is sufficient for most/all
            # If supply is good, I can be slightly less aggressive, but still competitive
            if highest_prev_bid >= DAILY_SALARY * 0.8 and my_hp < 8: # If high bids exist and I'm not super healthy
                base_bid = max(base_bid, highest_prev_bid * 0.95) # Match closely but try to save a bit
            else:
                base_bid = max(base_bid, avg_prev_bid * 0.9) # Slightly less than average

    # Ensure bid is at least a minimal amount to stay in the game
    min_bid_to_stay_relevant = DAILY_SALARY * 0.2
    base_bid = max(base_bid, min_bid_to_stay_relevant)

    # Final bid cannot exceed current budget
    final_bid = min(my_budget, base_bid)

    # Ensure bid is not negative and handles zero budget cases
    if final_bid <= 0 and my_budget > 0:
        final_bid = my_budget # Bid all remaining budget if it's positive but calculated bid was zero/negative
    elif final_bid < 0:
        final_bid = 0.0 # Should not happen with min() against budget, but as a safeguard

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        # Enough water for me, bid low
        if day_context['supply'] >= WATER_REQ:
            return min(my_status['budget'], DAILY_SALARY * 0.2)
        else: # Not enough water, still bid low as no competition
            return min(my_status['budget'], DAILY_SALARY * 0.3)

    # Base bid, ensuring competitiveness for my high water requirement
    base_bid = DAILY_SALARY * 0.7 # 105.0

    # Adjust base bid based on my HP for urgency
    if my_status['hp'] <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95 # 142.5
    elif my_status['hp'] <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.85 # 127.5

    # Look at yesterday's situation (Trace) for opponent bidding patterns
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    final_bid = base_bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.85: # Very high competition yesterday
            if my_status['hp'] > 4: # If my HP is good, I can afford to back off slightly
                # Try to save budget, but stay somewhat competitive relative to average
                final_bid = min(final_bid, max(DAILY_SALARY * 0.6, avg_prev_bid * 0.9))
            else: # My HP is low, I must compete aggressively
                final_bid = max(final_bid, highest_prev_bid + 5.0) # Bid above to secure
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # Moderate competition yesterday
            final_bid = max(final_bid, highest_prev_bid + 2.0) # Bid slightly above to stay competitive
        else: # Low competition yesterday
            final_bid = max(final_bid, highest_prev_bid + 10.0) # Try to secure water cheaply, but ensure I get it

    # Adjust bid based on supply scarcity relative to total demand
    total_water_needed_by_all = (num_alive_opponents + 1) * WATER_REQ
    
    if day_context['supply'] < total_water_needed_by_all: # Supply is tight
        final_bid *= 1.1 # Increase bid by 10%
    elif day_context['supply'] >= total_water_needed_by_all * 1.5: # Supply is abundant
        final_bid *= 0.9 # Decrease bid by 10%

    # Ensure bid doesn't exceed budget and meets minimum requirement
    final_bid = min(my_status['budget'], final_bid)
    final_bid = max(1.0, final_bid) # Minimum bid is 1.0

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
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 4:
                return min(my_status['budget'], DAILY_SALARY * 0.5)
            else:
                return min(my_status['budget'], DAILY_SALARY * 0.9)
        
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            return min(my_status['budget'], max(DAILY_SALARY * 0.7, highest_prev_bid + 2.0))
        
        else:
            if my_status['hp'] > 6:
                return min(my_status['budget'], DAILY_SALARY * 0.4)
            else:
                return min(my_status['budget'], max(DAILY_SALARY * 0.6, highest_prev_bid + 1.0))

    current_day = day_context['day']
    if current_day <= EPISODE_DAYS / 3:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
    elif current_day <= EPISODE_DAYS * 2 / 3:
        return min(my_status['budget'], DAILY_SALARY * 0.7)
    else:
        return min(my_status['budget'], DAILY_SALARY * 0.8)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)
    num_active_players = num_alive_opponents + 1 # Myself + opponents

    if num_alive_opponents == 0:
        return min(my_current_budget, DAILY_SALARY * 0.1)

    # --- Determine base bid based on HP and day --- 
    # Start with a competitive bid, adjust based on HP
    if my_current_hp <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95
    elif my_current_hp <= 5: # Low HP
        base_bid = DAILY_SALARY * 0.85
    elif my_current_hp <= 7: # Medium HP
        base_bid = DAILY_SALARY * 0.75
    else: # Healthy HP
        base_bid = DAILY_SALARY * 0.65

    # Adjust bid based on day progression (become more aggressive towards the end)
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        if my_current_hp > 5: # If healthy, ensure survival but use budget
             base_bid = max(base_bid, DAILY_SALARY * 0.9)
        else: # If not healthy, bid max
             base_bid = max(base_bid, DAILY_SALARY * 0.98)
    elif current_day >= EPISODE_DAYS - 4: # Last 4 days
        if my_current_hp > 5:
            base_bid = max(base_bid, DAILY_SALARY * 0.8)

    # --- Incorporate opponent's previous day bids --- 
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.9: # Very high competition
            if my_current_hp > 5:
                base_bid = max(base_bid, highest_prev_bid + 5)
            else:
                base_bid = max(base_bid, highest_prev_bid + 10)
        elif highest_prev_bid >= DAILY_SALARY * 0.75: # Moderate competition
            base_bid = max(base_bid, highest_prev_bid + 2)
        else: # Low competition, still aim to win
            base_bid = max(base_bid, highest_prev_bid + 1)

    # --- Adjust bid based on supply scarcity --- 
    num_water_units = int(current_supply // WATER_REQ)

    if num_water_units <= num_active_players: # Scarce water, high competition
        if my_current_hp <= 5: # Critical or low HP, bid very high
            base_bid = max(base_bid, DAILY_SALARY * 0.98)
        else: # Healthy HP, but still need to compete
            base_bid = max(base_bid, DAILY_SALARY * 0.85)
    elif num_water_units >= num_active_players * 2: # Abundant water
        if my_current_hp > 5: # If healthy, try to save money
            base_bid = min(base_bid, DAILY_SALARY * 0.5)
        else: # Still need to secure water, but might not need to bid highest
            base_bid = min(base_bid, DAILY_SALARY * 0.7)

    final_bid = min(my_current_budget, base_bid)
    return max(1.0, final_bid)
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

    # If no opponents are alive, bid minimally to save budget.
    if num_alive_opponents == 0:
        return min(my_status['budget'], 1.0)

    days_remaining = EPISODE_DAYS - day_context['day'] + 1

    # Base bid: Aggressive starting point, as only one agent can typically get full water.
    # Alex and Eric showed bids often above 80% of salary.
    current_bid = DAILY_SALARY * 0.85

    # Adjust bid based on my HP and recent water status
    if my_status['hp'] <= 2: # Critical HP
        current_bid = DAILY_SALARY * 0.99
    elif my_status['hp'] <= 5: # Low HP
        current_bid = DAILY_SALARY * 0.95
    elif my_status['no_water_days'] > 0: # Missed water yesterday
        current_bid = max(current_bid, DAILY_SALARY * 0.9)

    # React to yesterday's highest bid from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If an opponent bid high yesterday, we need to exceed it to secure water.
        # Add a small margin to outbid.
        if highest_prev_bid >= DAILY_SALARY * 0.7: # If competitive bidding happened
            current_bid = max(current_bid, highest_prev_bid + 5.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # If moderate bidding
            current_bid = max(current_bid, highest_prev_bid + 2.0)
        # If highest_prev_bid was very low, still maintain a strong bid,
        # as not all opponents might be bidding low (e.g., Alex).

    # End game strategy: If few days left and HP is not full, bid high.
    # If HP is critical and it's the last few days, go almost all in.
    if days_remaining <= 3:
        if my_status['hp'] <= 5:
            current_bid = my_status['budget'] * 0.99
        elif my_status['hp'] <= 8:
            current_bid = max(current_bid, DAILY_SALARY * 0.9) # Ensure high bid in endgame

    # Cap bid by current budget
    final_bid = min(my_status['budget'], current_bid)

    # Ensure bid is at least 1.0 (minimum valid bid)
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimally to secure water if supply is sufficient
    if not alive_opponents:
        if current_supply >= WATER_REQ:
            return min(my_budget, 1.0)
        else:
            # If supply is less than my requirement, I can't get full water anyway, bid low
            return min(my_budget, 1.0)

    # Determine a base bid - high due to water scarcity
    base_bid = DAILY_SALARY * 0.8 # Default aggressive bid

    # Adjust bid based on my HP
    if my_hp <= 2: # Critical HP
        base_bid = DAILY_SALARY * 1.0 # Bid full salary, up to budget
    elif my_hp <= 4: # Low HP
        base_bid = max(base_bid, DAILY_SALARY * 0.95)

    # Adjust bid based on game progression (end game)
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        base_bid = max(base_bid, DAILY_SALARY * 0.98) # Ensure high bid in endgame

    # Adjust bid based on opponent's previous day behavior
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were bidding very high, I need to exceed that
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            base_bid = max(base_bid, highest_prev_bid + 5.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.7:
            base_bid = max(base_bid, highest_prev_bid + 2.0)
        else:
            # If low bids, still maintain a solid bid given the scarcity
            base_bid = max(base_bid, DAILY_SALARY * 0.8)

    # Ensure bid does not exceed budget
    final_bid = min(my_budget, base_bid)

    # Ensure bid is at least 1.0 to participate if budget allows, otherwise 0
    if final_bid < 1.0 and my_budget >= 1.0:
        final_bid = 1.0
    elif my_budget == 0:
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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_supply = day_context['supply']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # --- Step 1: Determine base bid based on my health --- 
    base_bid = DAILY_SALARY * 0.55 # Default moderate bid

    if my_hp <= 2: # Critical health, bid very high
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 5: # Low health, bid high
        base_bid = DAILY_SALARY * 0.8
    elif my_hp >= 8: # Good health, can afford to save
        base_bid = DAILY_SALARY * 0.4

    # --- Step 2: Adjust bid based on supply scarcity --- 
    # Calculate how many players can get their full water requirement
    num_can_get_water = int(current_supply // WATER_REQ)
    total_players_competing = num_alive_opponents + 1 # Myself + alive opponents

    if num_can_get_water < total_players_competing:
        # Supply is scarce, competition is higher. Increase bid.
        if num_can_get_water <= 1: # Very scarce (only 0 or 1 person can get full water)
            base_bid = max(base_bid, DAILY_SALARY * 0.8)
        else: # Scarce, but more than one can get water
            base_bid = max(base_bid, DAILY_SALARY * 0.65)
    else:
        # Supply is abundant, can potentially bid lower if not under pressure
        if my_hp > 5: # Only lower if my HP is good
            base_bid = min(base_bid, DAILY_SALARY * 0.45)


    # --- Step 3: Adjust bid based on opponents' previous bids (previous_trace) --- 
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were aggressive yesterday, react
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Very high previous bids
            if my_hp <= 5: # If I need water, bid slightly above
                base_bid = max(base_bid, highest_prev_bid + 5)
            else: # If I'm healthy, try to be competitive but don't overspend
                base_bid = max(base_bid, highest_prev_bid * 0.95) # Try to get it cheaper, but still near
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderate previous bids
            base_bid = max(base_bid, highest_prev_bid + 2) # Slightly above to win
        else: # Low previous bids, try to win cheaply
            if my_hp > 7: # If healthy, try for a bargain
                base_bid = min(base_bid, highest_prev_bid + 1)
            else: # Still need to win
                base_bid = max(base_bid, highest_prev_bid + 5)


    # --- Step 4: Final bid calculation and constraints --- 
    bid = base_bid

    # Ensure bid does not exceed budget
    bid = min(bid, my_budget)

    # Ensure bid is at least 1.0
    bid = max(1.0, bid)

    # If it's the last day and I'm desperate, bid everything
    if current_day == EPISODE_DAYS and my_hp <= 2:
        bid = my_budget

    return bid
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
    num_alive_opponents = len(alive_opponents)

    # Base bid - a moderate amount to secure water
    bid = DAILY_SALARY * 0.6

    # Strategy 1: If no opponents, bid minimally to save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    # Strategy 2: Aggressive bid if HP is critically low
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.98)
    elif my_status['hp'] <= 5:
        bid = max(bid, DAILY_SALARY * 0.85)

    # Strategy 3: Adjust bid based on supply scarcity
    # If supply is less than what everyone needs, competition is high
    total_water_needed_approx = WATER_REQ * (num_alive_opponents + 1)
    if day_context['supply'] < total_water_needed_approx:
        bid = max(bid, DAILY_SALARY * 0.75)
    
    # If supply is very tight, e.g., only enough for 1-2 players
    if day_context['supply'] < WATER_REQ * 1.5:
        bid = max(bid, DAILY_SALARY * 0.9)

    # Strategy 4: React to yesterday's highest bid from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents are bidding very high, we need to compete
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            bid = max(bid, highest_prev_bid + 5)
        # If opponents are bidding moderately, slightly outbid them
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            bid = max(bid, highest_prev_bid + 2)
        # If opponents are bidding low, ensure we still get water but don't overpay too much
        else:
            bid = max(bid, highest_prev_bid + 10)

    # Strategy 5: Increase aggression in the late game
    if day_context['day'] >= EPISODE_DAYS - 3:
        bid = max(bid, DAILY_SALARY * 0.9)

    # Final adjustments
    # Ensure bid does not exceed budget or daily salary
    bid = min(bid, my_status['budget'])
    bid = min(bid, DAILY_SALARY)

    # Ensure bid is positive
    bid = max(bid, 0.1)

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

    competitive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev_trace = opp.get('previous_trace', {})
            if opp_id == "Bob" or opp_id == "Alex" or (prev_trace and prev_trace.get('bid', 0) > 0.01):
                competitive_opponents.append(opp)

    base_bid = DAILY_SALARY * 0.5

    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5:
        base_bid = DAILY_SALARY * 0.75
    elif my_status['hp'] >= 8:
        base_bid = DAILY_SALARY * 0.4

    if day_context['supply'] < WATER_REQ * 1.5:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    elif day_context['supply'] < WATER_REQ * 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.65)
    else:
        base_bid = min(base_bid, DAILY_SALARY * 0.5)

    yesterday_competitive_bids = []
    for opp in competitive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_competitive_bids.append(prev['bid'])

    if yesterday_competitive_bids:
        highest_prev_bid = max(yesterday_competitive_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, highest_prev_bid * 1.05)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            base_bid = max(base_bid, highest_prev_bid + 5)
        else:
            base_bid = max(base_bid, highest_prev_bid * 1.1)

    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.85)
    elif day_context['day'] <= 2:
        if my_status['hp'] > 5:
            base_bid = min(base_bid, DAILY_SALARY * 0.6)

    final_bid = min(my_status['budget'], base_bid)
    final_bid = max(0.01, final_bid)

    if my_status['no_water_days'] > 0 and my_status['hp'] <= 1:
        final_bid = my_status['budget']

    return final_bid
"""
