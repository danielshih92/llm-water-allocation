# ============================================================
# Experiment: exp_102
# Agent: Cindy
# Source: exp_102
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimally to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid, reflecting the high competition for scarce water
    base_bid = DAILY_SALARY * 0.6 # e.g., 90

    # Adjust bid based on my HP (survival priority)
    current_bid = base_bid
    if my_status['hp'] <= 2: # Critical state: 1 or 2 days left without water
        current_bid = DAILY_SALARY * 0.95 # Bid very aggressively (e.g., 142.5)
    elif my_status['hp'] == 3: # Low HP: 3 days left
        current_bid = DAILY_SALARY * 0.8 # Bid aggressively (e.g., 120)
    # Else, current_bid remains base_bid (90) for healthy HP

    # Adjust bid based on opponent's previous highest bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.8: # If highest opponent bid was high (e.g., >= 120)
            # If I'm healthy, try to slightly outbid or maintain pressure
            if my_status['hp'] > 3:
                current_bid = max(current_bid, highest_prev_bid + 2.0)
            else: # If I'm desperate, bid even higher to win
                current_bid = max(current_bid, highest_prev_bid + 5.0)
        elif highest_prev_bid < DAILY_SALARY * 0.5: # If opponents were bidding relatively low (e.g., < 75)
            # If I'm healthy, I can try to save money by bidding just above them
            if my_status['hp'] > 3:
                current_bid = min(current_bid, highest_prev_bid + 1.0)
                current_bid = max(current_bid, DAILY_SALARY * 0.4) # Ensure a floor (e.g., 60)
            else: # If I'm desperate, still bid high to secure water
                current_bid = max(current_bid, highest_prev_bid + 10.0) # Ensure I win if they underbid

    # Ensure the bid does not exceed budget
    final_bid = min(my_status['budget'], current_bid)
    # Ensure a minimum bid (e.g., 15) to always participate meaningfully
    final_bid = max(final_bid, DAILY_SALARY * 0.1)

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

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 5:
                return min(my_status['budget'], DAILY_SALARY * 0.75)
            else:
                return min(my_status['budget'], DAILY_SALARY * 0.9)
        else:
            base_bid = max(DAILY_SALARY * 0.5, avg_prev_bid + 5)

            num_players_competing = len(alive_opponents) + 1
            available_water_slots = int(day_context['supply'] // WATER_REQ)
            
            if available_water_slots < num_players_competing:
                base_bid *= 1.1
            elif available_water_slots > num_players_competing * 1.5:
                base_bid *= 0.9

            return min(my_status['budget'], base_bid)
    else:
        base_bid = DAILY_SALARY * 0.6

        num_players_competing = len(alive_opponents) + 1
        available_water_slots = int(day_context['supply'] // WATER_REQ)

        if available_water_slots < num_players_competing:
            base_bid *= 1.1
        elif available_water_slots > num_players_competing * 1.5:
            base_bid *= 0.9

        return min(my_status['budget'], base_bid)
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

    if not alive_opponents:
        return min(my_status['budget'], 1.0) if my_status['budget'] > 0 else 0.0

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    my_bid = DAILY_SALARY * 0.5

    # Aggressive bidding if desperate (low HP or missed water yesterday)
    if my_status['hp'] <= WATER_REQ * 2 or my_status['no_water_days'] > 0:
        my_bid = DAILY_SALARY * 0.9

    # React to opponents' previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.6:
            my_bid = max(my_bid, highest_prev_bid + 2.0)
        else:
            my_bid = max(my_bid, DAILY_SALARY * 0.55)

    # Adjust based on supply scarcity and number of competitors
    total_water_needed_by_competitors = sum(opp['water_requirement'] for opp in alive_opponents)
    total_demand = WATER_REQ + total_water_needed_by_competitors

    if day_context['supply'] < total_demand * 0.8 and len(alive_opponents) > 0:
        my_bid = max(my_bid, DAILY_SALARY * 0.8)

    # End game pressure
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 3 and my_status['hp'] <= WATER_REQ * 3:
        my_bid = max(my_bid, DAILY_SALARY * 0.95)

    final_bid = min(my_status['budget'], my_bid)

    if final_bid <= 0 and my_status['budget'] > 0 and my_status['hp'] > 0:
        final_bid = 1.0
    elif my_status['budget'] <= 0:
        final_bid = 0.0

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_supply = day_context['supply']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to get water
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid based on my health
    if my_hp <= 2:
        # Critical HP, bid very aggressively
        base_bid = DAILY_SALARY * 1.1
    elif my_hp <= 5:
        # Low HP, bid aggressively
        base_bid = DAILY_SALARY * 0.9
    else:
        # Healthy HP, try to save budget, but still competitive
        base_bid = DAILY_SALARY * 0.7

    # Adjust bid based on supply: lower supply means higher competition
    # Scale factor from 1 (min supply) to 0 (max supply)
    supply_pressure_factor = (MAX_SUPPLY - current_supply) / (MAX_SUPPLY - MIN_SUPPLY)
    base_bid += supply_pressure_factor * (DAILY_SALARY * 0.15) # Add up to 15% of salary for supply pressure

    # Adjust bid based on opponents' previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents are bidding very high, react
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            if my_hp <= 5: # If I need water, outbid them slightly
                base_bid = max(base_bid, highest_prev_bid * 1.05)
            else: # If healthy, avoid bidding war or try to get water cheaper
                base_bid = min(base_bid, highest_prev_bid * 0.95) # Bid slightly below to test if they overbid
        elif highest_prev_bid < DAILY_SALARY * 0.5: # If opponents are bidding low
            if my_hp <= 5: # Still need water, bid slightly above them to secure it
                base_bid = max(base_bid, highest_prev_bid * 1.2)
            else: # Healthy, save money but still try to win if cheap
                base_bid = min(base_bid, DAILY_SALARY * 0.6) # Cap bid to avoid overspending on cheap water
    
    # Adjust bid based on day urgency (more urgent towards the end)
    day_urgency_factor = current_day / EPISODE_DAYS
    base_bid += day_urgency_factor * (DAILY_SALARY * 0.1) # Add up to 10% of salary for end-game urgency

    # Final bid must not exceed budget
    final_bid = min(base_bid, my_budget)

    # Ensure non-negative and a minimum bid if budget allows
    if my_budget <= 0:
        return 0.0
    return max(final_bid, 0.01) # Minimum bid to participate
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
    num_players_needing_water = len(alive_opponents) + 1 # Myself + alive opponents

    # If no opponents, bid minimal to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid
    current_bid = DAILY_SALARY * 0.5 # A moderate starting point

    # Adjust based on yesterday's highest bid to react to opponent pressure
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid > DAILY_SALARY * 0.7: # If yesterday's max bid was high
            current_bid = max(current_bid, highest_prev_bid * 1.05) # Try to outbid slightly
        elif highest_prev_bid < DAILY_SALARY * 0.4: # If yesterday's max bid was low
            current_bid = min(current_bid, highest_prev_bid * 1.1) # Don't bid too high unnecessarily
        else: # Moderate bids, slightly above max to win
            current_bid = max(current_bid, highest_prev_bid + 5)

    # Adjust based on my HP for survival
    if my_status['hp'] <= 2: # Critical HP, bid aggressively
        current_bid = max(current_bid, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4: # Low HP, bid higher
        current_bid = max(current_bid, DAILY_SALARY * 0.8)

    # Adjust based on supply scarcity
    # Calculate how many full water requirements can be met
    available_water_slots = int(day_context['supply'] // WATER_REQ)
    if available_water_slots < num_players_needing_water: # Supply is scarce, competition will be high
        if day_context['day'] < EPISODE_DAYS / 2: # Early game scarcity
            current_bid = max(current_bid, DAILY_SALARY * 0.85)
        else: # Late game scarcity, even more aggressive
            current_bid = max(current_bid, DAILY_SALARY * 0.9)
    else: # Supply is abundant, can bid lower to save budget
        current_bid = min(current_bid, DAILY_SALARY * 0.6)

    # Ensure bid is within budget and reasonable limits
    current_bid = max(0.0, current_bid) # Bid cannot be negative
    current_bid = min(my_status['budget'], current_bid) # Cannot bid more than budget
    current_bid = min(DAILY_SALARY * 1.2, current_bid) # Cap bid to prevent runaway spending, but allow slightly above salary if budget allows and desperate

    # If budget is very low and I need water, bid whatever is left
    if my_status['budget'] < DAILY_SALARY * 0.5 and my_status['hp'] < 5:
        current_bid = my_status['budget']

    return current_bid
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

    # If no opponents, bid a very low amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1, 5.0) # Ensure a minimum bid of 5.0 if budget allows

    # Calculate required water for everyone including me
    total_water_needed_units = (num_alive_opponents + 1) * WATER_REQ
    
    # Check if supply is scarce (less total water than needed for everyone to get their requirement)
    is_supply_scarce = day_context['supply'] < total_water_needed_units

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid
    # Start with a moderate bid, around half my daily salary
    base_bid = DAILY_SALARY * 0.55

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If yesterday's highest bid was very high, react aggressively
        if highest_prev_bid >= DAILY_SALARY * 0.9: # e.g., > 135
            base_bid = max(base_bid, highest_prev_bid + 5) # Try to outbid
        # If yesterday's highest bid was moderate, react to stay competitive
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # e.g., > 90
            base_bid = max(base_bid, highest_prev_bid + 1)
        # If yesterday's bids were low, be conservative but still competitive
        else:
            base_bid = min(base_bid, highest_prev_bid * 1.1)

    # Adjust bid based on my HP
    if my_status['hp'] <= 3: # Critical HP
        base_bid = max(base_bid, DAILY_SALARY * 1.2) # Bid very aggressively, potentially above salary
    elif my_status['hp'] <= 5: # Low HP
        base_bid = max(base_bid, DAILY_SALARY * 0.95) # Bid aggressively, close to salary
    
    # Adjust bid based on remaining days (end game)
    remaining_days = EPISODE_DAYS - day_context['day'] + 1
    if remaining_days <= 2 and my_status['hp'] > 0: # Last couple of days, push for survival
        base_bid = max(base_bid, DAILY_SALARY * 1.5) # Extremely aggressive if survival is at stake
    
    # Adjust bid based on supply scarcity
    if is_supply_scarce:
        base_bid *= 1.1 # Increase bid if water is scarce
    else: # Supply is abundant
        base_bid *= 0.9 # Decrease bid if water is abundant, but don't go too low

    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], base_bid)
    
    # Ensure a minimum bid to actually participate and potentially win
    final_bid = max(5.0, final_bid) # Minimum bid of 5.0

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']
    current_supply = day_context['supply']

    # 1. Emergency Mode: Low HP or consecutive no-water days
    if my_current_hp <= 2 or my_no_water_days >= 1:
        bid_amount = DAILY_SALARY * 0.95
        if highest_prev_bid > 0:
            bid_amount = max(bid_amount, highest_prev_bid + 5) # Try to outbid if possible
        return min(my_current_budget, bid_amount)

    # 2. End Game Pressure: Days are running out
    if current_day >= EPISODE_DAYS - 2:
        bid_amount = DAILY_SALARY * 0.8
        if highest_prev_bid > 0:
            bid_amount = max(bid_amount, highest_prev_bid + 3)
        return min(my_current_budget, bid_amount)

    # 3. General Strategy based on opponent behavior and supply
    base_bid = DAILY_SALARY * 0.55

    # Adjust based on yesterday's highest bid
    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents are very aggressive
            base_bid = max(base_bid, highest_prev_bid * 0.95) # Try to match or slightly undercut
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Opponents are moderately aggressive
            base_bid = max(base_bid, highest_prev_bid + 2) # Slightly outbid
        else: # Opponents are conservative
            base_bid = max(base_bid, highest_prev_bid + 1) # Small increment

    # Adjust based on supply scarcity
    # Calculate how many water units are available for my requirement
    water_units_available = current_supply // WATER_REQ
    num_bidders = len(alive_opponents) + 1 # Include myself

    if water_units_available < num_bidders: # Not enough for everyone
        base_bid *= 1.15 # Increase bid significantly
    elif water_units_available >= num_bidders + 1: # Plenty of water
        base_bid *= 0.9 # Decrease bid slightly

    # Adjust based on day progression (mid-game pressure)
    if current_day > EPISODE_DAYS / 2 and current_day < EPISODE_DAYS - 2:
        base_bid *= 1.05

    final_bid = min(my_current_budget, base_bid)
    
    # Ensure bid is at least 1 if budget allows, to signal participation
    if final_bid <= 0 and my_current_budget > 0:
        final_bid = 1.0

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
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']

    base_value_of_water = DAILY_SALARY

    # Adjust bid based on desperation
    if my_hp <= 2 or my_no_water_days >= 1:
        target_bid = base_value_of_water * 1.2 # Extremely desperate, bid very high
    elif my_hp <= 4:
        target_bid = base_value_of_water * 1.0 # Desperate, bid full salary
    else:
        target_bid = base_value_of_water * 0.6 # Not desperate, start with a moderate bid

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1) # No opponents, bid minimum to win

    yesterday_bids = []
    highest_prev_bid = 0.0
    bob_is_alive_and_aggressive = False

    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                bid_value = prev_trace['bid']
                yesterday_bids.append(bid_value)
                if bid_value > highest_prev_bid:
                    highest_prev_bid = bid_value
                
                # Check for Bob specifically (known high bidder from meta-round context)
                if opp_id == "Bob" and bid_value >= base_value_of_water * 0.8:
                    bob_is_alive_and_aggressive = True

    if yesterday_bids:
        if bob_is_alive_and_aggressive or highest_prev_bid >= base_value_of_water * 0.85:
            # High competition detected (either Bob or generally high bids)
            if my_hp > 3 and my_no_water_days == 0:
                # Can afford to be conservative if not desperate
                target_bid = min(target_bid, base_value_of_water * 0.7) 
            else:
                # Must compete, try to outbid
                target_bid = max(target_bid, highest_prev_bid + 5.0)
        elif highest_prev_bid < base_value_of_water * 0.4:
            # Opponents are bidding low (likely Alex, David, Eric types)
            target_bid = max(target_bid, highest_prev_bid + 10.0) # Try to win cheaply but surely
        else:
            # Moderate competition
            target_bid = max(target_bid, highest_prev_bid + 2.0)
    
    days_remaining = EPISODE_DAYS - current_day
    if days_remaining <= 2 and my_hp <= 5: # End game desperation
        target_bid = max(target_bid, base_value_of_water * 1.5) # Bid very aggressively to survive final days

    final_bid = min(my_budget, target_bid)
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
    EPISODE_DAYS = 10 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    remaining_days = EPISODE_DAYS - day_context['day'] + 1

    # Base bid: a strong competitive bid, designed to be competitive against Alex's average
    current_bid = DAILY_SALARY * 0.92 # ~138

    # Adjust bid based on my HP and no_water_days
    if my_status['hp'] <= 2: # Critical HP
        current_bid = max(current_bid, DAILY_SALARY * 1.1) # Bid above salary
        if remaining_days > 1: 
            current_bid = min(current_bid, my_status['budget'] * 0.95)
        else: # Last day, go all in
            current_bid = my_status['budget']
    elif my_status['hp'] <= 4: # Low HP
        current_bid = max(current_bid, DAILY_SALARY * 1.0) # Bid full salary
    elif my_status['no_water_days'] > 0: # Missed water yesterday, need it today
        current_bid = max(current_bid, DAILY_SALARY * 0.98) # Ensure high bid

    # Adjust bid based on supply scarcity
    num_possible_full_slots = int(day_context['supply'] // WATER_REQ)
    
    if num_possible_full_slots < (num_alive_opponents + 1): # If supply is tight
        current_bid *= 1.05 
    elif num_possible_full_slots >= (num_alive_opponents + 1) + 1: # If supply is very abundant
        current_bid *= 0.98 

    # Adjust bid based on opponent's previous bids (yesterday's trace)
    highest_prev_bid = 0
    alex_prev_bid = 0

    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                opp_bid = prev_trace['bid']
                highest_prev_bid = max(highest_prev_bid, opp_bid)
                if opp_id == 'Alex':
                    alex_prev_bid = opp_bid

    # React to Alex specifically if he's alive and bid yesterday
    if alex_prev_bid > 0:
        if alex_prev_bid >= DAILY_SALARY * 1.0: # Alex bid very aggressively
            current_bid = max(current_bid, alex_prev_bid + 5) 
        elif alex_prev_bid > DAILY_SALARY * 0.85: # Alex bid competitively
            current_bid = max(current_bid, alex_prev_bid + 2)
    
    # Also react to highest overall previous bid if it's significant and higher than current_bid
    if highest_prev_bid > DAILY_SALARY * 0.95 and highest_prev_bid > current_bid:
        current_bid = highest_prev_bid + 1

    # Ensure bid is within budget and positive
    final_bid = max(1.0, min(my_status['budget'], current_bid))
    
    # Last day logic: if I need water to survive, bid aggressively
    if remaining_days == 1:
        if my_status['hp'] > 0: 
            final_bid = min(my_status['budget'], max(final_bid, DAILY_SALARY * 1.0))
        else: # Already failing, bid minimally
            final_bid = min(my_status['budget'], DAILY_SALARY * 0.1)
    
    # Ensure a minimum competitive bid if there are opponents and I have budget
    if final_bid < DAILY_SALARY * 0.5 and num_alive_opponents > 0 and my_status['budget'] > DAILY_SALARY * 0.5:
        final_bid = max(final_bid, DAILY_SALARY * 0.5)

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

    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimally to survive
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # --- Determine base bid --- 
    # A moderate starting point, adjusted by current day progress
    base_bid = DAILY_SALARY * 0.5

    # Early game (first 3 days) - be a bit conservative unless HP is bad
    if current_day <= 3 and my_status['hp'] > 5:
        base_bid = DAILY_SALARY * 0.45

    # --- Adjust bid based on my HP --- 
    if my_status['hp'] <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.98
    elif my_status['hp'] <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.85
    elif my_status['hp'] <= 6 and current_day > EPISODE_DAYS / 2: # Mid-game low HP
        base_bid = DAILY_SALARY * 0.75

    # --- Adjust bid based on water scarcity and opponent pressure --- 
    total_water_needed_by_all = sum(o['water_requirement'] for o in alive_opponents) + WATER_REQ
    
    # Calculate how many water requirements can be met
    num_reqs_met_by_supply = int(current_supply // WATER_REQ)

    # Number of active players including myself
    num_active_players = len(alive_opponents) + 1

    # If water is very scarce compared to total requirements
    if current_supply < total_water_needed_by_all * 0.8: # Significant scarcity
        base_bid *= 1.15 # Increase bid

    # If supply can barely cover everyone, or not everyone
    if num_reqs_met_by_supply < num_active_players:
        # Water is competitive, increase bid
        base_bid *= 1.25
        # If I have low HP and water is scarce, bid even higher for survival
        if my_status['hp'] <= 4:
             base_bid = max(base_bid, DAILY_SALARY * 0.95)

    # --- React to yesterday's opponent bids --- 
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents bid very high yesterday, we might need to match or exceed
        if max_yesterday_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, max_yesterday_bid * 1.05) # Try to outbid slightly
        elif max_yesterday_bid >= DAILY_SALARY * 0.6:
            base_bid = max(base_bid, max_yesterday_bid + 5) # Slightly above
        
        # If opponents are generally bidding low, we can be more conservative unless my HP is critical
        if avg_yesterday_bid < DAILY_SALARY * 0.4 and my_status['hp'] > 5:
            base_bid = min(base_bid, DAILY_SALARY * 0.4)

    # --- Adjust based on remaining budget and days --- 
    remaining_days = EPISODE_DAYS - current_day

    # If it's a late game and I have low HP, bid very aggressively
    if remaining_days <= 2 and my_status['hp'] <= 5:
        base_bid = DAILY_SALARY * 0.99 # Almost full salary for survival
    elif remaining_days <= 1 and my_status['hp'] > 0: # Last day, ensure survival if possible
        base_bid = DAILY_SALARY * 0.99

    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], base_bid)
    
    # Ensure a minimum bid if budget allows, to stay competitive
    if final_bid < DAILY_SALARY * 0.1 and my_status['budget'] >= DAILY_SALARY * 0.1:
        final_bid = DAILY_SALARY * 0.1
    
    # If budget is very low, bid whatever is left
    if my_status['budget'] < 10 and my_status['budget'] > 0:
        final_bid = my_status['budget']
    elif my_status['budget'] <= 0:
        return 0.0

    return final_bid
"""
