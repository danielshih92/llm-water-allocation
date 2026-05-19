# ============================================================
# Experiment: exp_041
# Agent: Cindy
# Source: exp_041
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimal to win water
    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid based on opponent's previous actions or a default
    base_bid_from_opponents = DAILY_SALARY * 0.5 # Default conservative bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If yesterday was competitive (highest bid was relatively high), try to outbid slightly
        if highest_prev_bid >= DAILY_SALARY * 0.7:
            base_bid_from_opponents = max(highest_prev_bid + 1, avg_prev_bid * 1.1)
        # If yesterday wasn't very competitive, bid slightly above average but conserve
        else:
            base_bid_from_opponents = max(avg_prev_bid * 1.05, DAILY_SALARY * 0.4)

    # Adjust bid based on my own status (HP and no_water_days)
    my_bid = base_bid_from_opponents

    # Critical state: one day away from death
    if my_status['no_water_days'] >= my_status['hp'] - 1:
        my_bid = max(my_bid, DAILY_SALARY * 0.95) # Bid very aggressively
    # High need: two days away from death
    elif my_status['no_water_days'] >= my_status['hp'] - 2:
        my_bid = max(my_bid, DAILY_SALARY * 0.8) # Bid aggressively
    # Normal state: healthy HP
    else:
        my_bid = max(my_bid, DAILY_SALARY * 0.5) # Ensure a minimum reasonable bid even if opponents bid low

    # Ensure bid is within budget and at least 1.0
    my_bid = min(my_status['budget'], my_bid)
    my_bid = max(1.0, my_bid)

    return my_bid
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid
    bid = DAILY_SALARY * 0.5 # Default moderate bid

    # 1. Prioritize survival based on HP
    if my_hp <= 2: # Critical HP
        bid = DAILY_SALARY * 0.95
    elif my_hp <= 5: # Low HP
        bid = DAILY_SALARY * 0.75
    elif my_hp <= 7: # Mid-low HP
        bid = DAILY_SALARY * 0.65

    # 2. End of game pressure
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last few days, must survive
        bid = max(bid, DAILY_SALARY * 0.9)
    elif remaining_days <= 5: # Mid-late game
        bid = max(bid, DAILY_SALARY * 0.7)

    # 3. React to opponent's previous bids (from current meta-round's yesterday)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Very aggressive opponents
            if my_hp <= 5: # If I'm low HP, I must compete
                bid = max(bid, highest_prev_bid + 5)
            else: # If healthy, match but don't overspend too much
                bid = max(bid, highest_prev_bid * 1.02) # Slightly above
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderate opponents
            bid = max(bid, highest_prev_bid + 1)
        else: # Low bidders
            bid = max(bid, highest_prev_bid * 1.1)

    # 4. Competition density and supply scarcity
    # If supply is very tight (e.g., only one slot for 13 water)
    # Note: current_supply is float, WATER_REQ is int. Comparison works fine.
    if current_supply < WATER_REQ * 1.5 and num_alive_opponents >= 1: 
        if my_hp <= 6: # Need water more
            bid = max(bid, DAILY_SALARY * 0.8) # High bid
        else: # Can afford to be slightly less aggressive
            bid = max(bid, DAILY_SALARY * 0.6)

    # If many opponents are still alive
    if num_alive_opponents >= 3:
        bid = max(bid, DAILY_SALARY * 0.6) # Increase bid due to more competition
    elif num_alive_opponents == 2:
        bid = max(bid, DAILY_SALARY * 0.55)


    # Final bid adjustments
    final_bid = min(my_budget, bid)

    # Special logic for full HP or no budget
    if my_budget == 0:
        final_bid = 0
    elif my_hp == 10: # If full HP, I don't *need* water. Can save budget.
        if my_budget > DAILY_SALARY * 0.2 and num_alive_opponents > 0: # If I have budget and competition, bid low to get cheap water
            final_bid = min(final_bid, DAILY_SALARY * 0.1) # Bid max 15
        else: # If full HP and low budget or no competition, bid 0
            final_bid = 0
    elif my_hp < 10 and my_budget > 0: # If not full HP and have budget, always bid at least 1
        final_bid = max(final_bid, 1)
    
    # Ensure bid is not negative
    final_bid = max(0.0, final_bid)

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

    # Base bid strategy based on HP
    if my_status['hp'] <= 2:
        bid = DAILY_SALARY * 0.95 # Critical HP, bid very aggressively
    elif my_status['hp'] <= 4:
        bid = DAILY_SALARY * 0.8 # Low HP, bid aggressively
    else:
        bid = DAILY_SALARY * 0.55 # Healthy HP, bid moderately

    # Adjust bid based on yesterday's opponent bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If my HP is critical or low, I need to secure water
        if my_status['hp'] <= 4:
            # Ensure we bid above the highest previous bid, with a safety margin
            bid = max(bid, highest_prev_bid + 5)
        else:
            # If healthy, be competitive but try not to overpay much
            # Bid slightly above highest_prev_bid if it's not too high
            if highest_prev_bid < DAILY_SALARY * 0.7:
                bid = max(bid, highest_prev_bid + 2)
            else:
                # If opponents are bidding very high even when I'm healthy,
                # try to stay close without overpaying significantly.
                bid = max(bid, highest_prev_bid * 0.95)

    # Adjust for supply scarcity: if fewer water slots than active players
    num_possible_winners = int(day_context['supply'] / WATER_REQ)
    num_active_players = len(alive_opponents) + 1

    if num_active_players > num_possible_winners and num_possible_winners > 0:
        # If competition is high, increase bid slightly
        bid *= 1.05

    # Adjust for late game pressure
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2-3 days
        if my_status['hp'] <= 5: # If still struggling late game
            bid = DAILY_SALARY * 1.0 # Bid very aggressively, potentially more than salary if budget allows
        else:
            bid = DAILY_SALARY * 0.75 # Still aggressive but not max if healthy

    # Ensure bid does not exceed current budget and is at least 1.0
    final_bid = min(my_status['budget'], bid)
    final_bid = max(1.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid a minimal amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # --- Base Bid Strategy ---
    # Start with a competitive base bid. Given water scarcity, it needs to be relatively high.
    current_bid = DAILY_SALARY * 0.7 

    # HP-based adjustment: If HP is low, bid more aggressively
    if my_status['hp'] <= 3: 
        current_bid = DAILY_SALARY * 0.95 
    elif my_status['hp'] <= 5: 
        current_bid = DAILY_SALARY * 0.85 
    
    # Day-based adjustment: Be more aggressive towards the end of the episode
    if day_context['day'] >= EPISODE_DAYS - 2: 
        current_bid = max(current_bid, DAILY_SALARY * 0.95) 
    elif day_context['day'] >= EPISODE_DAYS // 2: 
        current_bid = max(current_bid, DAILY_SALARY * 0.85) 

    # Supply-based adjustment: If supply is very low, increase bid
    if day_context['supply'] <= MIN_SUPPLY + 2: 
        current_bid *= 1.1 
    elif day_context['supply'] >= MAX_SUPPLY - 2 and my_status['hp'] > 5: 
        current_bid *= 0.95 

    # --- Opponent-based adjustment (yesterday's bids) ---
    final_bid = current_bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If opponents were bidding very high yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.9: 
            if my_status['hp'] <= 3: 
                final_bid = max(current_bid, highest_prev_bid + 7)
            else: 
                final_bid = max(current_bid, highest_prev_bid + 3)
        # If opponents were bidding moderately high
        elif highest_prev_bid >= DAILY_SALARY * 0.7: 
            final_bid = max(current_bid, highest_prev_bid + 2)
        # If opponents were bidding relatively low
        else:
            final_bid = max(current_bid, highest_prev_bid + 1)
    
    # Final adjustments
    # Ensure bid does not exceed budget
    final_bid = min(final_bid, my_status['budget'])

    # Ensure a minimum bid if budget allows, to avoid bidding 0 and dying unnecessarily
    if my_status['budget'] > 0 and final_bid < DAILY_SALARY * 0.1:
        final_bid = max(final_bid, DAILY_SALARY * 0.1)

    # Cap bid at a reasonable maximum if not critical HP, to prevent overspending too early.
    if my_status['hp'] > 3:
        final_bid = min(final_bid, DAILY_SALARY * 1.05)
    
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

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to secure water and save budget
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    # --- Determine base bid based on my state and general game conditions ---
    base_bid = DAILY_SALARY * 0.5 # Default moderate bid

    # Aggression based on my HP and no_water_days
    if my_hp <= 3 or my_no_water_days > 0:
        base_bid = DAILY_SALARY * 0.95 # Critical state, bid very aggressively
    elif my_hp <= 5:
        base_bid = DAILY_SALARY * 0.75 # Low health, bid high
    elif my_hp >= 8 and my_budget > DAILY_SALARY * 3: # Good health and good budget
        # Can afford to be slightly less aggressive if conditions allow
        base_bid = DAILY_SALARY * 0.45

    # Adjust based on supply scarcity (relative to total potential demand)
    total_water_needed_by_all = WATER_REQ # My requirement
    for opp in alive_opponents:
        total_water_needed_by_all += opp['water_requirement']

    # If supply is less than total needed, competition is high
    if total_water_needed_by_all > 0 and current_supply < total_water_needed_by_all:
        # Scale up bid based on how scarce it is, max 1.5x original base_bid
        scarcity_factor = 1.0 + (1.0 - (current_supply / total_water_needed_by_all)) * 0.5 
        base_bid *= scarcity_factor
    elif total_water_needed_by_all > 0 and current_supply >= total_water_needed_by_all * 1.5:
        # Abundant supply, can potentially bid lower
        base_bid *= 0.85

    # --- Incorporate opponent's previous day's bids (immediate reaction) ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents were very aggressive yesterday, consider matching/exceeding
        if max_prev_bid > DAILY_SALARY * 0.8:
            # If I need water, try to outbid the max
            if my_hp <= 7 or my_no_water_days > 0:
                base_bid = max(base_bid, max_prev_bid + 5) # Bid slightly above
            else: # If I'm healthy, I might not need to match their aggression
                base_bid = max(base_bid, max_prev_bid * 0.9) # Still acknowledge, but try to save
        elif avg_prev_bid > DAILY_SALARY * 0.4: # Moderate average bid
            base_bid = max(base_bid, avg_prev_bid * 1.05) # Bid slightly above average
    
    # --- End game strategy ---
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last two days
        if my_hp <= 5: # Critical health, go all in
            base_bid = DAILY_SALARY * 0.99
        elif my_budget > DAILY_SALARY * 3: # Good budget, secure win
            base_bid = max(base_bid, DAILY_SALARY * 0.85)
        else: # Try to survive
            base_bid = max(base_bid, DAILY_SALARY * 0.6)
    
    # Ensure bid does not exceed budget and is positive
    final_bid = min(my_budget, base_bid)
    final_bid = max(final_bid, 0.01) # Minimum bid to participate

    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    EPISODE_DAYS = 10
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    day_progress_factor = 1 + (day_context['day'] - 1) / (EPISODE_DAYS - 1) * 0.2 if EPISODE_DAYS > 1 else 1.0
    supply_pressure_factor = 1 + (MAX_SUPPLY - day_context['supply']) / (MAX_SUPPLY - MIN_SUPPLY) * 0.1 if (MAX_SUPPLY - MIN_SUPPLY) > 0 else 1.0

    base_competitive_bid = DAILY_SALARY * 0.55 * day_progress_factor * supply_pressure_factor

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    my_bid = base_competitive_bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 5:
                my_bid = DAILY_SALARY * 0.3 * day_progress_factor
            else:
                my_bid = DAILY_SALARY * 0.95 * day_progress_factor * supply_pressure_factor
        else:
            my_bid = max(base_competitive_bid, highest_prev_bid + 5.0)

    if my_status['hp'] <= 2:
        my_bid = DAILY_SALARY * 0.98 * day_progress_factor * supply_pressure_factor
    elif my_status['hp'] <= 4:
        my_bid = max(my_bid, DAILY_SALARY * 0.85 * day_progress_factor * supply_pressure_factor)
    elif my_status['hp'] <= 7:
        my_bid = max(my_bid, DAILY_SALARY * 0.7 * day_progress_factor * supply_pressure_factor)

    final_bid = max(1.0, min(my_status['budget'], my_bid))

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

    # If no opponents, bid minimum to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a baseline or highest previous bid
    # If no previous bids or all were 0, assume a moderate base bid to start
    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    
    # If highest_prev_bid is still 0 (e.g., all opponents bid 0 or no trace), set a default
    if highest_prev_bid == 0:
        highest_prev_bid = DAILY_SALARY * 0.4 # A reasonable starting bid

    # Calculate remaining days
    remaining_days = EPISODE_DAYS - day_context['day']

    # Strategy based on my HP and opponent behavior
    # Critical HP: Bid very high to survive
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    # Low HP: Bid aggressively
    if my_status['hp'] <= 4:
        # Try to outbid the highest previous bid, or ensure a strong bid
        return min(my_status['budget'], max(highest_prev_bid + 10, DAILY_SALARY * 0.85))

    # React to very high previous bids (likely from Alex)
    if highest_prev_bid >= DAILY_SALARY * 0.80: # e.g., 120 for 150 salary
        # If I have a good HP buffer and it's not endgame, slightly outbid
        if my_status['hp'] > 5 and remaining_days > 2:
             return min(my_status['budget'], highest_prev_bid + 5)
        else: # Lower HP or endgame, be more aggressive
            return min(my_status['budget'], highest_prev_bid + 15)

    # If highest previous bid was moderate, bid slightly above it or a solid amount
    if highest_prev_bid > DAILY_SALARY * 0.40: # e.g., > 60 for 150 salary
        return min(my_status['budget'], max(highest_prev_bid + 2, DAILY_SALARY * 0.6))

    # Default bid: moderate, conserving budget, if no strong threats or low HP
    return min(my_status['budget'], DAILY_SALARY * 0.5)
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

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    bid_amount = DAILY_SALARY * 0.55

    if my_status['hp'] <= 2:
        bid_amount = DAILY_SALARY * 0.99
    elif my_status['hp'] <= 5:
        bid_amount = DAILY_SALARY * 0.85
    else:
        num_full_water_slots = int(day_context['supply'] // WATER_REQ)

        if num_full_water_slots >= num_alive_opponents + 1:
            bid_amount = DAILY_SALARY * 0.3
        elif num_full_water_slots >= 2:
            if highest_prev_bid > DAILY_SALARY * 0.8:
                bid_amount = max(bid_amount, highest_prev_bid + 0.5)
            else:
                bid_amount = DAILY_SALARY * 0.5
        else:
            if highest_prev_bid > DAILY_SALARY * 0.8:
                bid_amount = max(bid_amount, highest_prev_bid + 1.0)
            elif highest_prev_bid > DAILY_SALARY * 0.6:
                bid_amount = max(bid_amount, highest_prev_bid + 0.5)
            else:
                bid_amount = DAILY_SALARY * 0.65

    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2:
        if my_status['hp'] <= 5:
            bid_amount = DAILY_SALARY * 0.99
        elif my_status['hp'] >= 8:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.7)

    final_bid = min(my_status['budget'], bid_amount)

    if final_bid <= 0.01 and my_status['budget'] > 0:
        final_bid = 1.0

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

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If I cannot get my water requirement, bid 0.
    if current_supply < WATER_REQ:
        return 0.0

    # If no opponents, bid minimally to get water
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Base bid - start with a moderate amount
    base_bid = DAILY_SALARY * 0.5

    # Adjust bid based on HP (survival priority)
    if my_hp <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    elif my_no_water_days > 0: # Missed water recently, need to secure it
        base_bid = max(base_bid, DAILY_SALARY * 0.7)

    # Adjust bid based on day (later days are more critical)
    if current_day >= EPISODE_DAYS * 0.7: # Last 30% of days
        base_bid = max(base_bid, DAILY_SALARY * 0.75)
    elif current_day >= EPISODE_DAYS * 0.5: # Mid-game
        base_bid = max(base_bid, DAILY_SALARY * 0.6)

    # React to yesterday's opponent bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were very aggressive, I need to raise my bid
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, highest_prev_bid * 1.05) # Bid slightly higher than max
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            base_bid = max(base_bid, highest_prev_bid + 5) # Bid a bit higher to outbid

    # Adjust bid based on supply and number of competitors
    # If supply is tight and there are multiple competitors, increase bid
    if current_supply <= WATER_REQ + 5 and num_alive_opponents >= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.85)

    # Ensure bid does not exceed budget and is not negative
    final_bid = min(my_budget, base_bid)
    
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid strategy
    bid = DAILY_SALARY * 0.55 # Default moderate bid

    # CRITICAL: If HP is low or I missed water yesterday, bid aggressively
    if my_status['hp'] <= 3 or my_status['no_water_days'] > 0:
        bid = DAILY_SALARY * 0.95
    # If HP is getting low mid-to-late game, increase bid
    elif my_status['hp'] <= 5 and day_context['day'] > EPISODE_DAYS / 2:
        bid = DAILY_SALARY * 0.8
    # If HP is okay, but it's late in the game, stay competitive
    elif day_context['day'] >= EPISODE_DAYS * 0.7:
        bid = DAILY_SALARY * 0.7

    # Adjust bid based on opponents' previous behavior (exploitation)
    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents bidding very high
            if my_status['hp'] > 7 and my_status['no_water_days'] == 0: # If healthy, don't necessarily match extreme bids
                bid = max(bid, DAILY_SALARY * 0.75) # Stay competitive but don't overspend
            else: # Not healthy enough to risk, must be competitive
                bid = max(bid, highest_prev_bid + 5) # Bid slightly above
        elif highest_prev_bid < DAILY_SALARY * 0.5: # Opponents bidding low
            bid = max(bid, DAILY_SALARY * 0.5, highest_prev_bid + 10) # Win cheaply but surely
        else: # Moderate opponent bids
            bid = max(bid, highest_prev_bid + 2) # Bid slightly above to secure

    # Consider supply: With supply [15, 25] and WATER_REQ=13, only 1 full water slot.
    # Competition is always high for full water. Reinforce higher bids if opponents are present.
    if len(alive_opponents) >= 1:
        if my_status['hp'] <= 5 or my_status['no_water_days'] > 0:
            bid = max(bid, DAILY_SALARY * 0.85) # Aggressive if critical
        else:
            bid = max(bid, DAILY_SALARY * 0.65) # Competitive otherwise

    # Final bid must not exceed budget
    final_bid = min(my_status['budget'], bid)
    
    # Ensure a minimum bid if budget allows, to stay in the game
    if my_status['budget'] > 0 and final_bid < DAILY_SALARY * 0.1:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.1)
    elif my_status['budget'] > 0 and final_bid == 0: # If final_bid somehow became 0 but budget exists
        final_bid = my_status['budget'] * 0.1 # Bid a small fraction of remaining budget

    return final_bid
"""
