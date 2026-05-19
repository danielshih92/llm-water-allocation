# ============================================================
# Experiment: exp_043
# Agent: Cindy
# Source: exp_043
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15.0
    MAX_SUPPLY = 25.0

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # --- Step 1: Determine a base bid --- 
    # If no opponents, bid minimal to save budget
    if num_alive_opponents == 0:
        return min(my_budget, 1)

    # Base bid based on HP urgency
    if my_hp <= 1: # Critical HP
        base_bid = DAILY_SALARY * 0.95
    elif my_hp == 2: # Very low HP
        base_bid = DAILY_SALARY * 0.80
    elif my_hp == 3: # Low HP
        base_bid = DAILY_SALARY * 0.65
    else: # Healthy HP (hp > 3)
        base_bid = DAILY_SALARY * 0.50

    # Adjust base bid based on supply scarcity
    # Normalize supply to a 0-1 range where 0 is MIN_SUPPLY and 1 is MAX_SUPPLY
    if MAX_SUPPLY == MIN_SUPPLY:
        normalized_supply = 0.5 # Default to middle if range is zero
    else:
        normalized_supply = (current_supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    
    # If supply is in the lower half of the range, increase bid; if upper half, decrease slightly.
    if normalized_supply < 0.5:
        base_bid *= (1 + (0.5 - normalized_supply) * 0.5) # Up to 25% increase
    else:
        base_bid *= (1 - (normalized_supply - 0.5) * 0.2) # Up to 10% decrease

    # --- Step 2: Adjust bid based on opponent's previous bids from 'previous_trace' ---
    highest_prev_opp_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_opp_bid = max(highest_prev_opp_bid, prev['bid'])

    final_bid = base_bid

    if highest_prev_opp_bid > 0:
        # If yesterday's highest bid was very high, it indicates strong competition or an opponent in distress.
        if highest_prev_opp_bid >= DAILY_SALARY * 0.8: # Very high previous bid (e.g., >= 120)
            if my_hp <= 2: # I also need water desperately, bid to win
                final_bid = max(final_bid, highest_prev_opp_bid + 2.0)
            else: # I'm healthy, try to be competitive but don't overspend
                final_bid = max(final_bid, highest_prev_opp_bid * 0.9)
        elif highest_prev_opp_bid >= DAILY_SALARY * 0.5: # Moderate previous bid (e.g., >= 75)
            final_bid = max(final_bid, highest_prev_opp_bid + 1.0) # Bid slightly higher to win
        else: # Low previous bid (e.g., < 75)
            final_bid = max(final_bid, highest_prev_opp_bid * 1.1) # Be slightly more aggressive than low bids

    # Ensure bid is within budget and non-negative. Minimum bid is 1.
    final_bid = min(my_budget, max(1.0, final_bid))

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
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_budget, 1.0) # Bid minimally if alone

    base_bid = DAILY_SALARY * 0.65

    # Adjust bid based on my own status (survival priority)
    if my_hp <= 2: # Very low HP
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    elif my_no_water_days > 0: # Missed water yesterday
        base_bid = max(base_bid, DAILY_SALARY * 0.75)

    # Adjust bid based on opponents' previous behavior
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        total_water_needed_by_competitors = sum(o['water_requirement'] for o in alive_opponents) + WATER_REQ
        is_supply_scarce = current_supply < total_water_needed_by_competitors

        if is_supply_scarce:
            if highest_prev_bid >= DAILY_SALARY * 0.8:
                base_bid = max(base_bid, highest_prev_bid + 5.0)
            elif highest_prev_bid >= DAILY_SALARY * 0.6:
                base_bid = max(base_bid, highest_prev_bid + 2.0)
            else:
                base_bid = max(base_bid, highest_prev_bid * 1.05)
        else:
            if highest_prev_bid >= DAILY_SALARY * 0.8:
                base_bid = max(base_bid, highest_prev_bid * 0.95)
            elif highest_prev_bid < DAILY_SALARY * 0.5:
                base_bid = max(base_bid, highest_prev_bid + 1.0)
            else:
                base_bid = max(base_bid, highest_prev_bid * 1.01)

    # Adjust bid based on remaining days (end-game pressure)
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif remaining_days <= 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.75)

    final_bid = min(my_budget, base_bid)
    final_bid = max(1.0, final_bid) if my_budget > 0 else 0.0

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
    current_day = day_context['day']
    current_supply = day_context['supply']

    # If I am the only one left, bid minimally to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's winning bids from alive opponents
    yesterday_winning_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        # Only consider bids that actually won water as a benchmark
        if prev and prev.get('bid') is not None and prev.get('status') == 'won':
            yesterday_winning_bids.append(prev['bid'])

    # Base bid calculation
    base_bid = DAILY_SALARY * 0.55 # A moderate starting bid

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] >= 8 and my_status['budget'] > DAILY_SALARY * 2: # Good HP and budget, can afford to save
        base_bid = DAILY_SALARY * 0.45

    # Adjust bid based on highest previous winning bid
    if yesterday_winning_bids:
        highest_prev_bid = max(yesterday_winning_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.8: # If highest bid was very high
            if my_status['hp'] <= 3: # If I'm critical, I must try to win
                base_bid = max(base_bid, highest_prev_bid + 5.0)
            else: # Otherwise, try to be competitive but not reckless
                base_bid = max(base_bid, highest_prev_bid * 0.95) # Try to get it for slightly less or match
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # If moderate
            base_bid = max(base_bid, highest_prev_bid + 2.0) # Bid slightly above to secure water
        else: # If previous bids were low
            base_bid = max(base_bid, highest_prev_bid + 1.0) # Just slightly above

    # Adjust bid based on supply scarcity
    # Estimate total water needed by active players
    total_water_needed = WATER_REQ # My need
    for opp in alive_opponents:
        total_water_needed += opp['water_requirement']

    # If supply is very tight compared to estimated total demand
    if current_supply < total_water_needed * 0.8: 
        base_bid *= 1.1 # Increase bid
    elif current_supply > total_water_needed * 1.2: # If supply is abundant
        base_bid *= 0.9 # Decrease bid

    # Adjust bid based on remaining days - become more aggressive towards the end if needed
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_status['hp'] < 5: # Last few days, need to survive
        base_bid = max(base_bid, DAILY_SALARY * 0.9) # Ensure survival

    # Final bid must be within budget and positive
    final_bid = max(1.0, min(my_status['budget'], base_bid))

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

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Default conservative bid
    bid = DAILY_SALARY * 0.4

    if num_alive_opponents == 0:
        # If no opponents, bid minimally to secure water
        return min(my_budget, DAILY_SALARY * 0.1)

    # Analyze yesterday's bids from previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Adjust bid based on current HP
    if my_hp <= 2: # Critical HP
        bid = DAILY_SALARY * 0.95
        if highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid + 7) # Aggressively outbid
    elif my_hp <= 4: # Low HP
        bid = DAILY_SALARY * 0.8
        if highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid + 3)
    elif my_hp <= 7: # Moderate HP
        bid = DAILY_SALARY * 0.6
        if highest_prev_bid > 0:
            # If supply is tight, be more competitive
            if current_supply < (num_alive_opponents + 1) * WATER_REQ:
                bid = max(bid, highest_prev_bid + 1)
            else: # Enough for more, try to be smart
                bid = max(bid, highest_prev_bid * 0.95) # Slight undercut or match
    else: # High HP
        bid = DAILY_SALARY * 0.5
        if highest_prev_bid > 0:
            # If supply is tight for me and one opponent (e.g., supply < 2*WATER_REQ)
            if current_supply < (2 * WATER_REQ):
                bid = max(bid, highest_prev_bid * 0.9) # Still competitive but less aggressive
            else: # Supply is ample, try to save
                bid = min(bid, highest_prev_bid * 0.8) # Significantly undercut
                bid = max(bid, DAILY_SALARY * 0.3) # Ensure a floor

    # Adjust bid based on remaining days (end game pressure)
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 3: # Last few days
        if my_hp < 6: # If HP is also low, become very aggressive
            bid = max(bid, DAILY_SALARY * 0.9)
            if highest_prev_bid > 0:
                 bid = max(bid, highest_prev_bid + 10)
        else: # HP is okay, but still late game
            bid = max(bid, DAILY_SALARY * 0.7)
            if highest_prev_bid > 0:
                 bid = max(bid, highest_prev_bid + 5)

    # Adjust bid based on supply scarcity
    # If supply is very low (e.g., only enough for one player)
    if current_supply < WATER_REQ * 1.5: # Highly competitive for first slot
        bid = max(bid, DAILY_SALARY * 0.85) # Aggressive base
        if highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid + 8)
    # If supply is ample (enough for two or more players)
    elif current_supply >= WATER_REQ * 2:
        if my_hp > 5: # If healthy, try to save
            bid = min(bid, DAILY_SALARY * 0.6)
            if highest_prev_bid > 0:
                bid = min(bid, highest_prev_bid * 0.85) # Try to undercut
        else: # If HP is low, still secure water but don't overpay if not needed
            bid = max(bid, DAILY_SALARY * 0.5)
            if highest_prev_bid > 0:
                bid = max(bid, highest_prev_bid * 0.9)

    # Final check: ensure bid is not negative and within budget
    bid = max(0.0, bid)
    bid = min(my_budget, bid)

    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    potential_slots = int(day_context['supply'] / WATER_REQ)
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    if my_status['no_water_days'] >= 1:
        desperation_bid = DAILY_SALARY * 0.9 + (my_status['no_water_days'] * 5)
        return min(my_status['budget'], desperation_bid)
    
    eric_bid_yesterday = 0.0
    highest_prev_bid_among_alive = 0.0
    
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid_value = prev['bid']
                highest_prev_bid_among_alive = max(highest_prev_bid_among_alive, bid_value)
                if opp_id == "Eric":
                    eric_bid_yesterday = bid_value

    base_bid = DAILY_SALARY * 0.55
    
    if eric_bid_yesterday > 0:
        if potential_slots <= 1:
             base_bid = max(base_bid, eric_bid_yesterday + 10)
        else:
            base_bid = max(base_bid, eric_bid_yesterday + 2)
    elif highest_prev_bid_among_alive > 0:
        if potential_slots <= 1:
            base_bid = max(base_bid, highest_prev_bid_among_alive + 7)
        else:
            base_bid = max(base_bid, highest_prev_bid_among_alive + 1)

    num_alive_opponents = len(alive_opponents)
    
    if num_alive_opponents >= potential_slots:
        competition_factor = 1.0 + (num_alive_opponents - potential_slots) * 0.1
        base_bid = max(base_bid, DAILY_SALARY * 0.6 * competition_factor)
        
    if my_status['no_water_days'] == 0:
        base_bid = min(base_bid, DAILY_SALARY * 0.95)

    final_bid = min(my_status['budget'], base_bid)
    
    return max(0.0, final_bid)
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

    # Determine initial bid based on my status
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.75
    else:
        base_bid = DAILY_SALARY * 0.5

    # Adjust bid based on overall supply and demand
    total_water_demand = WATER_REQ
    for opp in alive_opponents:
        total_water_demand += opp['water_requirement']

    if day_context['supply'] < total_water_demand:
        base_bid += DAILY_SALARY * 0.15
    elif day_context['supply'] >= total_water_demand + WATER_REQ * 2:
        if my_status['hp'] > 4:
            base_bid -= DAILY_SALARY * 0.1

    # Adjust bid based on opponents' previous bids (yesterday's trace)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, highest_prev_bid + 1.0)
        elif highest_prev_bid < DAILY_SALARY * 0.3:
            if my_status['hp'] > 2 and my_status['no_water_days'] == 0:
                base_bid = min(base_bid, highest_prev_bid + 5.0)

    # Final bid constraints
    final_bid = min(my_status['budget'], base_bid)
    
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        final_bid = min(final_bid, DAILY_SALARY * 1.1)
    else:
        final_bid = min(final_bid, DAILY_SALARY * 1.0)

    if final_bid <= 0.0 and my_status['budget'] > 0:
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

    current_day = day_context['day']
    current_supply = day_context['supply']

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        if my_hp < WATER_REQ:
            return min(my_budget, DAILY_SALARY * 0.9)
        else:
            return min(my_budget, DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    bid_value = DAILY_SALARY * 0.5

    if my_hp <= WATER_REQ:
        bid_value = DAILY_SALARY * 0.95
    elif my_no_water_days > 0:
        bid_value = DAILY_SALARY * 0.85
    elif my_hp <= 2 * WATER_REQ:
        bid_value = DAILY_SALARY * 0.7
    else:
        bid_value = DAILY_SALARY * 0.4

    total_agents = num_alive_opponents + 1
    if current_supply < total_agents * WATER_REQ:
        scarcity_factor = 1 - (current_supply / (total_agents * WATER_REQ))
        bid_value = max(bid_value, DAILY_SALARY * (0.6 + scarcity_factor * 0.3))

    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_hp <= WATER_REQ or my_no_water_days > 0:
                bid_value = max(bid_value, highest_prev_bid + 5.0)
            else:
                bid_value = max(bid_value, highest_prev_bid + 1.5)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            bid_value = max(bid_value, highest_prev_bid + 1.0)

    final_bid = min(my_budget, bid_value)
    final_bid = max(1.0, final_bid)

    return float(final_bid)
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
    
    # If no opponents, bid a minimal amount to get water
    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    # Handle Day 1 or no previous bids
    if day_context['day'] == 1:
        # On day 1, no previous trace exists. Bid a moderate amount.
        return min(my_status['budget'], DAILY_SALARY * 0.5)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine highest previous bid, or use a default if no valid bids yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    else:
        # If no opponents bid yesterday (e.g., all died or didn't bid), use a default competitive bid
        highest_prev_bid = DAILY_SALARY * 0.5

    # Bidding strategy based on my HP
    my_bid = 0.0

    if my_status['hp'] <= 3: # Desperate: Low HP
        # Bid aggressively to survive, try to outbid highest previous bid, but also ensure a floor
        my_bid = max(highest_prev_bid + 5, DAILY_SALARY * 0.9)
    elif my_status['hp'] <= 7: # Medium HP
        # Stay competitive, slightly above highest previous bid, or a solid base
        my_bid = max(highest_prev_bid + 2, DAILY_SALARY * 0.6)
    else: # High HP (my_status['hp'] > 7)
        # Conserve budget, but still aim for water. Bid slightly below or at highest, with a floor
        my_bid = max(highest_prev_bid * 0.9, DAILY_SALARY * 0.4)

    # Ensure bid doesn't exceed budget and is at least 1.0
    final_bid = min(my_status['budget'], my_bid)
    return max(final_bid, 1.0)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    # Calculate remaining days (used for end-game strategy)
    remaining_days = EPISODE_DAYS - day_context['day'] + 1

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid very low to save money
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # --- Identify key opponent (Bob) and his previous bid --- 
    # Based on LATEST METAROUND CONTEXT, Bob is the primary competitor.
    bob_alive = False
    bob_prev_bid = 0
    for opp_id, opp_data in opponents_status.items():
        if opp_id == "Bob" and opp_data['alive']:
            bob_alive = True
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bob_prev_bid = prev['bid']
            break # Found Bob, no need to check others for this specific logic

    # --- Determine base bid --- 
    # Default bid if no strong signals from opponents
    base_bid = DAILY_SALARY * 0.7 # 105

    if bob_alive:
        # If Bob is alive, we need to compete with him
        # Bob's average bid was around 103, max 180. We need to be competitive.
        if bob_prev_bid > DAILY_SALARY * 0.9: # Bob bid > 135 (very aggressive)
            base_bid = max(DAILY_SALARY * 1.0, bob_prev_bid + 5) # Bid at least 150, or slightly more than Bob
        elif bob_prev_bid > DAILY_SALARY * 0.6: # Bob bid > 90 (closer to his average)
            base_bid = max(DAILY_SALARY * 0.8, bob_prev_bid + 2) # Bid around 120, or slightly more than Bob
        else: # Bob bid relatively low yesterday (maybe he's conserving or struggling)
            base_bid = max(DAILY_SALARY * 0.7, bob_prev_bid + 1) # Bid around 105, or slightly more
    else:
        # Bob is not alive (or not found in opponents_status, implying not active).
        # Compete against other potentially weaker opponents.
        other_opponents_yesterday_bids = []
        for opp_id, opp_data in opponents_status.items():
            if opp_data['alive'] and opp_id != "Bob":
                prev = opp_data.get('previous_trace', {})
                if prev and prev.get('bid') is not None:
                    other_opponents_yesterday_bids.append(prev['bid'])
        
        if other_opponents_yesterday_bids:
            highest_other_bid = max(other_opponents_yesterday_bids)
            # Bid slightly above the highest of the remaining opponents
            base_bid = max(DAILY_SALARY * 0.5, highest_other_bid + 1) # Bid around 75, or slightly more
        else:
            # Only me or only very weak opponents left, bid conservatively
            base_bid = DAILY_SALARY * 0.4 # 60


    # --- Adjust bid based on my HP and remaining days --- 
    final_bid = base_bid

    # If HP is critical, bid very high
    if my_status['hp'] <= 2: # Very critical HP
        if remaining_days > 1: # Not the last day, try to save a little
            final_bid = min(my_status['budget'], DAILY_SALARY * 1.25) # Bid up to 187.5
        else: # Last day, go all in
            final_bid = my_status['budget']
    elif my_status['hp'] <= 5: # Low HP
        final_bid = min(my_status['budget'], base_bid * 1.1) # 10% more aggressive
    
    # Ensure bid is always positive and competitive enough to potentially win
    # A minimum bid to ensure participation and not lose due to bidding 0
    min_bid_threshold = DAILY_SALARY * 0.1 # 15
    final_bid = max(final_bid, min_bid_threshold)

    # The bid cannot exceed current budget
    return min(my_status['budget'], final_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
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

    max_yesterday_bid = DAILY_SALARY * 0.5 # Default if no previous bids or all bids were very low
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    num_active_players = len(alive_opponents) + 1
    total_water_demand = num_active_players * WATER_REQ
    current_supply = day_context['supply']

    is_high_competition = current_supply < total_water_demand
    is_very_high_competition = current_supply < (total_water_demand * 0.75)

    bid = DAILY_SALARY * 0.5 # Base moderate bid

    if my_status['hp'] <= 2: # Critical HP: Must win water
        bid = DAILY_SALARY * 0.95
        if is_very_high_competition:
            bid = max(bid, max_yesterday_bid * 1.1 + 10)
        elif is_high_competition:
            bid = max(bid, max_yesterday_bid * 1.05 + 5)
        else:
            bid = max(bid, max_yesterday_bid * 1.0 + 1) # Ensure we're slightly above even in low competition if HP is critical

    elif my_status['hp'] <= 4: # Low HP: Need water, but less critical
        bid = DAILY_SALARY * 0.75
        if is_very_high_competition:
            bid = max(bid, max_yesterday_bid * 1.05 + 5)
        elif is_high_competition:
            bid = max(bid, max_yesterday_bid * 1.02 + 3)
        else:
            bid = max(bid, max_yesterday_bid * 0.95) # Try to get it cheaper if not very competitive

    else: # Healthy HP: Can be more strategic
        bid = DAILY_SALARY * 0.55
        if is_very_high_competition:
            bid = max(bid, max_yesterday_bid * 1.0 + 1)
        elif is_high_competition:
            bid = max(bid, max_yesterday_bid * 0.95)
        else: # Low competition, try to bid lower
            bid = DAILY_SALARY * 0.4
            bid = max(bid, max_yesterday_bid * 0.8) # Ensure a reasonable bid even if yesterday's max was very low

    bid = max(1.0, bid) # Ensure bid is at least 1.0
    bid = min(my_status['budget'], bid) # Ensure bid does not exceed budget
    
    return bid
"""
