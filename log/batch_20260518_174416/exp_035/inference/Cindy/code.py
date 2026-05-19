# ============================================================
# Experiment: exp_035
# Agent: Cindy
# Source: exp_035
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

    # Base bid - a portion of daily salary
    bid = DAILY_SALARY * 0.5

    # Adjust bid based on my HP
    if my_status['hp'] <= 2:  # Critical HP, bid very high
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP, bid high
        bid = max(bid, DAILY_SALARY * 0.8)

    # Adjust bid based on supply and number of opponents
    current_supply = day_context['supply']
    # If supply is tight (less than what all alive agents need for their requirement)
    if current_supply < WATER_REQ * (num_alive_opponents + 1): 
        if my_status['hp'] <= 4: # Even more aggressive if supply is tight and HP is low
            bid = max(bid, DAILY_SALARY * 0.9)
        else:
            bid = max(bid, DAILY_SALARY * 0.6) # Increase bid if competition is high

    # Look at yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were bidding high, we might need to bid higher
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents were aggressive
            if my_status['hp'] <= 3:
                bid = max(bid, highest_prev_bid + 5) # Bid higher to ensure water
            else:
                bid = max(bid, DAILY_SALARY * 0.75) # Stay competitive
        else: # Opponents were not very aggressive
            bid = max(bid, highest_prev_bid + 1) # Bid slightly above to win

    # Ensure bid does not exceed budget and is not negative
    final_bid = min(my_status['budget'], bid)
    final_bid = max(0, final_bid)

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
    num_alive_opponents = len(alive_opponents)

    bid_amount = DAILY_SALARY * 0.5 # Default competitive bid

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Strategy based on HP and opponent's highest previous bid
    if my_status['hp'] <= 2: # Critical HP, bid aggressively
        bid_amount = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5: # Low HP, bid high
        bid_amount = DAILY_SALARY * 0.8
    elif my_status['no_water_days'] >= 1: # Missed water yesterday, need to secure it
        bid_amount = DAILY_SALARY * 0.9
    else: # Normal HP
        if highest_prev_bid > 0:
            # Try to outbid the highest previous bid by a small margin
            bid_amount = highest_prev_bid + 5
            # Ensure it's at least a reasonable amount if previous bid was very low
            bid_amount = max(bid_amount, DAILY_SALARY * 0.5)
        else:
            # If no previous bids, or all were 0, bid a competitive default
            bid_amount = DAILY_SALARY * 0.6

    # Further adjustment based on supply and number of competitors
    if day_context['supply'] < WATER_REQ * 2 and num_alive_opponents >= 2:
        # If supply is less than double my requirement and there are at least two competitors
        # This means competition for water is high
        if my_status['hp'] <= 5 or my_status['no_water_days'] >= 1:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.9) # Be very aggressive
        else:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.7) # Be aggressive but conserve if possible

    # Adjust bid for later days in the episode
    current_day = day_context['day']
    if current_day >= EPISODE_DAYS * 0.7: # Last few days
        bid_amount = max(bid_amount, DAILY_SALARY * 0.85) # Be more aggressive towards the end

    # Ensure bid does not exceed available budget
    final_bid = min(my_status['budget'], bid_amount)

    # Ensure a minimum bid if budget allows, to stay in the game
    if final_bid < DAILY_SALARY * 0.1 and my_status['budget'] >= DAILY_SALARY * 0.1:
        final_bid = DAILY_SALARY * 0.1
    elif my_status['budget'] == 0: # If budget is 0, bid 0
        final_bid = 0.0

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid minimally to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.05)

    # Analyze yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Determine bid based on my HP and opponent behavior

    # Critical HP: Must win to survive
    if my_status['hp'] <= 3:
        # Bid very aggressively. Try to outbid anyone.
        bid_multiplier = 0.95
        if EPISODE_DAYS - day_context['day'] <= 2: # Last 2 days
            bid_multiplier = 1.0 # Bid full salary if desperate
        
        # If opponents were bidding high, ensure we exceed their max.
        if highest_prev_bid > DAILY_SALARY * 0.8: # If high competition yesterday
            return min(my_status['budget'], max(DAILY_SALARY * bid_multiplier, highest_prev_bid + 5.0))
        else:
            return min(my_status['budget'], DAILY_SALARY * bid_multiplier)

    # Healthy HP: Try to win, but be mindful of budget
    else: # my_status['hp'] > 3
        # If highest previous bid was very high, we might need to match/exceed
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents are aggressive
            # Bid slightly above yesterday's highest to secure water, but not overspend
            return min(my_status['budget'], max(DAILY_SALARY * 0.7, highest_prev_bid + 2.0))
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderate competition
            # Bid slightly above yesterday's highest
            return min(my_status['budget'], max(DAILY_SALARY * 0.6, highest_prev_bid + 1.0))
        else: # Low competition or no significant bids yesterday
            # Bid a moderate amount, enough to win against low bidders, but save budget
            return min(my_status['budget'], max(DAILY_SALARY * 0.55, highest_prev_bid + 1.0))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If I'm the only one left, bid minimum to conserve budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], 1.0)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Default bid for healthy state
    my_bid = DAILY_SALARY * 0.55

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # HP-based adjustments
    if my_status['hp'] <= 2: # Critical HP
        my_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5: # Low HP
        my_bid = DAILY_SALARY * 0.8
    else: # Healthy HP (6-10)
        # Adjust based on highest previous bid from strong opponents
        if highest_prev_bid > DAILY_SALARY * 0.45: # If opponents are bidding significantly (e.g., David's range)
            my_bid = max(my_bid, highest_prev_bid + 5.0) # Try to outbid slightly
        elif highest_prev_bid > 0 and num_alive_opponents == 1: # Only one opponent, and they bid something
            my_bid = max(my_bid, highest_prev_bid + 1.0) # Just slightly outbid
        else: # Opponents generally bid low or 0, I can be less aggressive
            my_bid = DAILY_SALARY * 0.4 # Conserve budget a bit

    # Supply-based adjustments
    # Tight supply: only enough for one or barely two (supply values 15-19)
    if day_context['supply'] < WATER_REQ * 1.5: # supply < 19.5
        if my_status['hp'] <= 5: # Low HP, need to secure water
            my_bid = max(my_bid, DAILY_SALARY * 0.85) # Ensure high bid
        else:
            my_bid = max(my_bid, DAILY_SALARY * 0.65) # Still competitive
    # Generous supply: enough for two or more (supply values 20-25)
    elif day_context['supply'] >= WATER_REQ * 1.5: # supply >= 19.5 (i.e., 20-25)
        # If healthy and supply is good, can be slightly less aggressive
        if my_status['hp'] > 5 and my_bid > DAILY_SALARY * 0.6:
            my_bid *= 0.9 # Reduce slightly if already high

    # Ensure bid doesn't exceed budget
    final_bid = min(my_status['budget'], my_bid)

    # Ensure a minimum bid if budget allows and not alone
    if final_bid == 0 and my_status['budget'] > 0 and num_alive_opponents > 0:
        final_bid = min(my_status['budget'], 1.0) # Bid at least 1 if I have budget and opponents

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

    if not alive_opponents:
        return min(my_status['budget'], 1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.55

    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.75

    if yesterday_bids:
        max_prev_opp_bid = max(yesterday_bids)
        
        if max_prev_opp_bid >= DAILY_SALARY * 0.8 and my_status['hp'] > 2:
            base_bid = max(base_bid, max_prev_opp_bid + 5)
        elif max_prev_opp_bid < DAILY_SALARY * 0.4 and my_status['hp'] > 4:
            base_bid = min(base_bid, max_prev_opp_bid + 1)

    sum_opp_water_req = sum([o['water_requirement'] for o in alive_opponents])
    estimated_total_water_needed = sum_opp_water_req + WATER_REQ

    if day_context['supply'] < estimated_total_water_needed:
        if base_bid < DAILY_SALARY * 0.8:
            base_bid *= 1.1
    elif day_context['supply'] > estimated_total_water_needed * 1.5:
        if my_status['hp'] > 4 and base_bid > DAILY_SALARY * 0.3:
            base_bid *= 0.9

    bid = min(base_bid, my_status['budget'])
    bid = min(bid, DAILY_SALARY * 1.05)
    bid = max(bid, 1)

    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    base_bid = DAILY_SALARY * 0.65 # Moderate starting bid

    # 1. Survival mode: If HP is low, bid aggressively
    if my_status['hp'] <= 3: # Critical HP
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5: # Low HP
        base_bid = DAILY_SALARY * 0.8

    # 2. Adjust based on supply scarcity
    # If supply is just enough for me or slightly more, competition will be high
    if day_context['supply'] <= WATER_REQ + 2: # Tight supply
        base_bid += DAILY_SALARY * 0.15 # Increase bid
    elif day_context['supply'] >= MAX_SUPPLY - 2: # Abundant supply
        # Only decrease if not in critical survival mode
        if my_status['hp'] > 5:
            base_bid *= 0.85

    # 3. React to opponent's previous bids
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest previous bid was very high, we might need to match or slightly exceed
        if highest_prev_bid > DAILY_SALARY * 0.8: # Aggressive previous bid
            if my_status['hp'] > 5: # Not in immediate danger, can be strategic
                base_bid = max(base_bid, highest_prev_bid * 0.95) # Try to get it cheaper if possible
            else: # In danger, must secure water
                base_bid = max(base_bid, highest_prev_bid + 5) # Bid slightly higher
        elif highest_prev_bid > DAILY_SALARY * 0.5: # Moderate previous bid
            base_bid = max(base_bid, highest_prev_bid + 1) # Bid slightly above

    # Ensure bid does not exceed daily salary significantly, unless absolutely necessary for survival
    if my_status['hp'] > 3:
        base_bid = min(base_bid, DAILY_SALARY * 1.1) # Don't go too crazy if HP is good
    else:
        base_bid = min(base_bid, DAILY_SALARY * 1.2) # Allow slight overspending of daily salary if critical

    # Final check: Ensure bid doesn't exceed available budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure bid is at least 0
    return max(0.0, final_bid)
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
    
    # If no opponents, bid minimally to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Determine total players who might bid for water
    num_potential_bidders = 1 # Me
    for opp in alive_opponents:
        num_potential_bidders += 1

    # Check for critical health or no water days
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        # Desperate situation, bid very high to survive
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid
    base_bid = DAILY_SALARY * 0.55 # A moderate bid

    # Adjust base bid based on supply scarcity if no clear opponent bidding pattern from yesterday
    if not yesterday_bids:
        # Given supply range [15,25] and WATER_REQ = 13:
        # If 2+ players, total demand (>=26) always exceeds max supply (25).
        # So water is always scarce if there are 2+ players.
        if num_potential_bidders >= 2:
            base_bid = DAILY_SALARY * 0.7 # Increase bid for scarcity
        else: # Only me, or only one other player but supply is abundant for both
            base_bid = DAILY_SALARY * 0.4 # Less competition, bid lower
        
        # Consider day progression for initial bid
        if day_context['day'] > EPISODE_DAYS / 2 and my_status['hp'] < 5:
            base_bid = max(base_bid, DAILY_SALARY * 0.8) # Late game, low hp, bid higher

        return min(my_status['budget'], base_bid)

    # React to yesterday's highest bid
    highest_prev_bid = max(yesterday_bids)

    # Aggressive opponent behavior detected (e.g., Alex)
    if highest_prev_bid >= DAILY_SALARY * 0.8: # Using 80% of salary as high threshold
        # If healthy, consider backing off to save budget and let opponents exhaust themselves
        if my_status['hp'] > 3: 
            # Bid low, save budget, assume I can afford to miss water for a day
            return min(my_status['budget'], DAILY_SALARY * 0.3)
        else:
            # Not healthy, must compete aggressively
            # Bid slightly higher than the highest previous bid to win
            return min(my_status['budget'], max(DAILY_SALARY * 0.95, highest_prev_bid + 5))
    
    # Moderate/Passive opponent behavior (e.g., Eric)
    else: # highest_prev_bid is less than 80% of salary
        # Bid slightly above the highest previous bid to win, but don't overspend
        # Ensure it's at least a reasonable amount (e.g., 50% of salary)
        bid_value = max(DAILY_SALARY * 0.5, highest_prev_bid + 5)
        
        # If it's late in the game and my HP is okay, maybe save a bit more
        if day_context['day'] > EPISODE_DAYS * 0.7 and my_status['hp'] > 5:
            bid_value = min(bid_value, DAILY_SALARY * 0.6) # Don't go too high if healthy late game

        return min(my_status['budget'], bid_value)
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

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Default bid if no specific conditions apply
    base_bid = DAILY_SALARY * 0.55 # Moderate bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # React to high competition from yesterday
        # Using 0.85 threshold (127.5 for my salary) to detect aggressive bidding
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # Healthy, but competition is high, need to be competitive to win
                base_bid = min(DAILY_SALARY * 0.9, highest_prev_bid + 5.0) # Bid to win, but cap it
            else: # Desperate, need water
                base_bid = DAILY_SALARY * 0.95 # Bid very high
        else: # Moderate or low competition yesterday
            # Bid slightly above highest previous bid to win, but ensure it's at least moderate
            base_bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 5.0)

    # Adjust bid based on current HP if no strong previous bid context or to ensure high bid when desperate
    if my_status['hp'] <= 2: # Very low HP, desperate
        base_bid = max(base_bid, DAILY_SALARY * 0.9) # Ensure bid is high enough

    # Final bid must not exceed current budget
    final_bid = min(my_status['budget'], base_bid)
    
    # Ensure bid is at least 1.0 to participate
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid just enough to get water and save money
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid strategy
    base_bid = DAILY_SALARY * 0.6 # Default moderate bid

    # Adjust based on my HP and no_water_days (urgency)
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        # Critical state: bid very aggressively, potentially more than daily salary
        base_bid = DAILY_SALARY * 1.2
    elif my_status['hp'] <= 4:
        # Struggling: bid high
        base_bid = DAILY_SALARY * 0.9

    # Adjust based on competition (yesterday's highest bid)
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If an opponent bid very high, we need to be competitive
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Example threshold: 80% of my salary
            if my_status['hp'] <= 4: # If I'm struggling or critical
                base_bid = max(base_bid, highest_prev_bid + 10.0) # Bid higher than them
            else: # If I'm stable, still be competitive but try to save a bit
                base_bid = max(base_bid, highest_prev_bid + 2.0)
        elif highest_prev_bid < DAILY_SALARY * 0.5: # If opponents bid low
            if my_status['hp'] > 4: # If I'm stable, try to bid lower to save
                base_bid = min(base_bid, DAILY_SALARY * 0.5)
    
    # Adjust based on supply scarcity and number of competitors
    available_slots_for_me = int(day_context['supply'] // WATER_REQ)
    
    # If supply is tight (not enough for everyone + me), increase bid
    if available_slots_for_me <= len(alive_opponents) + 1:
        if my_status['hp'] <= 4: # More aggressive if critical
            base_bid = base_bid * 1.1
        else: # Slightly aggressive if stable
            base_bid = base_bid * 1.05
    
    # Ensure bid does not exceed budget and is at least 1
    final_bid = min(my_status['budget'], base_bid)
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_players = len(alive_opponents) + 1 # Including myself

    # --- Base bid strategy based on supply and competition ---
    supply_per_player = day_context['supply'] / num_alive_players
    
    if supply_per_player < WATER_REQ * 0.7: # Very scarce supply
        base_bid = DAILY_SALARY * 1.3 # Bid very high
    elif supply_per_player < WATER_REQ: # Scarce supply
        base_bid = DAILY_SALARY * 1.0 # Bid at least my salary
    elif supply_per_player < WATER_REQ * 1.5: # Moderate supply
        base_bid = DAILY_SALARY * 0.8 # Bid moderately
    else: # Ample supply
        base_bid = DAILY_SALARY * 0.6 # Bid conservatively

    # --- Adjust bid based on my HP ---
    # This part can override or boost the base_bid if my HP is critical
    bid_from_hp = base_bid # Start with the base bid
    if my_status['hp'] <= 1: # Critical HP (will die next day without water)
        bid_from_hp = DAILY_SALARY * 2.0 # Bid extremely high
    elif my_status['hp'] <= 3: # Low HP
        bid_from_hp = DAILY_SALARY * 1.5 # Bid very aggressively
    elif my_status['hp'] <= 5: # Moderate low HP
        bid_from_hp = max(base_bid, DAILY_SALARY * 1.1) # Ensure it's at least 1.1x salary
    elif my_status['hp'] >= 8: # Good HP, can afford to save
        bid_from_hp = min(base_bid, DAILY_SALARY * 0.5) # Try to save, but don't go too low if competition is high
    
    bid = bid_from_hp

    # --- Incorporate opponent's previous bids ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents are bidding very high, I might need to exceed that
        if highest_prev_bid > DAILY_SALARY * 1.1: # If highest bid was significantly above my salary
            bid = max(bid, highest_prev_bid + 15) # Bid significantly higher
        elif highest_prev_bid > DAILY_SALARY * 0.8: # If highest bid was moderately above salary
            bid = max(bid, highest_prev_bid + 7) # Bid slightly higher
        # If highest_prev_bid is low, my calculated 'bid' (based on HP/supply) should be sufficient.
    
    # --- Final adjustments ---
    final_bid = min(my_status['budget'], bid)
    final_bid = max(final_bid, 0.01) # Minimum bid to participate

    return final_bid
"""
