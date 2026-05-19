# ============================================================
# Experiment: exp_065
# Agent: Cindy
# Source: exp_065
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_SUPPLY = 25.0 # Ensure float for calculations
    MIN_SUPPLY = 15.0 # Ensure float for calculations

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o_id, o in opponents_status.items() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If I'm the only one alive, bid minimal to save money
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Base bid strategy: a fraction of daily salary
    base_bid = DAILY_SALARY * 0.6 # 90

    # Adjust bid based on my HP
    if my_hp <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95 # Bid very aggressively (142.5)
    elif my_hp == 3: # Low HP
        base_bid = DAILY_SALARY * 0.8 # Bid aggressively (120)
    elif my_hp == 4: # Moderate HP
        base_bid = DAILY_SALARY * 0.7 # Bid moderately (105)
    # If HP is 5, use the base_bid (90)

    # Adjust bid based on supply scarcity
    # Normalize supply: (current_supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    # This gives a value from 0 (min supply) to 1 (max supply).
    # If supply is low (closer to 0), increase bid. If high (closer to 1), decrease bid.
    supply_ratio = (current_supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_adjustment_range = DAILY_SALARY * 0.2 # Max 20% salary adjustment
    # Add more if supply is low (supply_ratio is low), less if supply is high
    base_bid += supply_adjustment_range * (1 - supply_ratio)

    # Opponent analysis using previous_trace (if available and not Day 1)
    highest_prev_bid = 0.0
    opponent_struggling_hp = False

    if current_day > 1: # Traces are available from Day 2 onwards
        for opp in alive_opponents:
            prev_trace = opp.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                highest_prev_bid = max(highest_prev_bid, prev_trace['bid'])
                if opp['hp'] <= 2: # Opponent is in critical HP
                    opponent_struggling_hp = True

        if highest_prev_bid > 0:
            # If I'm low on HP or an opponent is struggling (expect high bid from them)
            if my_hp <= 3 or opponent_struggling_hp:
                # Try to slightly outbid the highest previous bid, but not excessively.
                bid_to_beat = highest_prev_bid + (DAILY_SALARY * 0.05) # Add 5% of salary
                base_bid = max(base_bid, bid_to_beat)

    final_bid = base_bid

    # Ensure bid is at least a minimum amount
    min_bid_threshold = 1.0
    final_bid = max(final_bid, min_bid_threshold)

    # Ensure bid does not exceed my budget
    final_bid = min(final_bid, my_budget)

    # If my HP is max and supply is very generous, and no strong competition, I can afford to bid less.
    # This is a refinement to save money when conditions are ideal.
    if my_hp == 5 and current_supply >= MAX_SUPPLY - 2 and not opponent_struggling_hp and highest_prev_bid < (DAILY_SALARY * 0.7):
        final_bid = min(final_bid, DAILY_SALARY * 0.5) # Try to get water for half salary if conditions are good

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Determine base bid aggressiveness
    # Default aggressive bid, considering Alex and Eric's high bids
    base_bid = DAILY_SALARY * 0.75

    # Adjustment for critical situations
    if my_hp <= 2: # Very low HP, absolute must win
        base_bid = DAILY_SALARY * 0.99
    elif my_no_water_days >= 2: # Missed two days, critical
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4 or my_no_water_days >= 1: # Low HP or missed one day, strong need
        base_bid = max(base_bid, DAILY_SALARY * 0.85)
    elif my_hp >= 9: # High HP, can afford to be less aggressive, but still competitive
        base_bid = DAILY_SALARY * 0.6

    # Look at yesterday's bids from opponents to react
    highest_prev_opp_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_opp_bid = max(highest_prev_opp_bid, prev['bid'])

    # React to highest previous opponent bid
    if highest_prev_opp_bid > 0:
        if my_hp <= 4 or my_no_water_days >= 1: # I need water, try to beat their high bid
            base_bid = max(base_bid, highest_prev_opp_bid + 5)
        elif my_hp >= 9 and highest_prev_opp_bid >= DAILY_SALARY * 0.8: # Good HP, they overbid
            # Let them exhaust budget if I don't desperately need water
            base_bid = min(base_bid, DAILY_SALARY * 0.5)
        else: # Normal HP, try to beat them slightly
            base_bid = max(base_bid, highest_prev_opp_bid + 1)

    # Adjust for end of game urgency
    days_left = EPISODE_DAYS - current_day
    if days_left <= 2 and my_hp < 9: # Last few days, need to secure survival
        base_bid = max(base_bid, DAILY_SALARY * 0.9)

    # Ensure bid does not exceed budget. This is the ultimate cap.
    final_bid = min(my_budget, base_bid)

    # Ensure a non-zero bid if budget allows to participate.
    if final_bid <= 0 and my_budget > 0:
        final_bid = 1
    elif final_bid < 0: # Should not happen with min(my_budget, base_bid)
        final_bid = 0

    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Default bid: start with a moderate bid
    bid = DAILY_SALARY * 0.55 # 82.5
    
    # If no opponents, bid low to save budget
    if not alive_opponents:
        return max(1.0, min(my_budget, DAILY_SALARY * 0.3))
        
    # Collect yesterday's bids and identify Eric
    yesterday_bids = []
    eric_is_alive = False
    eric_yesterday_bid = None
    
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            if opp_id == "Eric":
                eric_is_alive = True
            
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
                if opp_id == "Eric":
                    eric_yesterday_bid = prev['bid']

    # Determine if supply is competitive
    num_potential_winners = int(current_supply // WATER_REQ)
    is_supply_competitive = num_potential_winners < (len(alive_opponents) + 1)

    # --- Bidding Logic --- 

    # Critical survival: If HP is very low, bid almost full salary or more if needed
    if my_hp <= 2:
        bid = DAILY_SALARY * 0.95 # 142.5
        # If supply is competitive, be even more aggressive up to 105% of salary
        if is_supply_competitive:
            bid = min(my_budget, DAILY_SALARY * 1.05) # Cap at slightly above salary

    # Consider Eric's general aggressive behavior and yesterday's bid
    elif eric_is_alive:
        if is_supply_competitive:
            # If supply is tight, bid aggressively against Eric
            bid = DAILY_SALARY * 0.9 # 135
            if eric_yesterday_bid is not None and eric_yesterday_bid > DAILY_SALARY * 0.8:
                bid = max(bid, eric_yesterday_bid + 5) # Try to outbid him slightly
            bid = min(bid, DAILY_SALARY * 1.05) # Cap at slightly above my salary
        else: # Supply is not competitive for the number of players, but Eric is there
            if eric_yesterday_bid is not None:
                if eric_yesterday_bid >= DAILY_SALARY * 0.85: # Eric bid very high yesterday
                    if my_hp > 3: # If I'm healthy, try to conserve, but still competitive
                        bid = DAILY_SALARY * 0.6 # 90
                    else: # If not healthy, must compete
                        bid = max(DAILY_SALARY * 0.9, eric_yesterday_bid + 1) # 135, or slightly more than Eric
                elif eric_yesterday_bid > DAILY_SALARY * 0.5: # Eric bid moderately
                    bid = max(DAILY_SALARY * 0.5, eric_yesterday_bid + 2) # 75, or slightly more
                else: # Eric bid low
                    bid = DAILY_SALARY * 0.4 # 60
            else: # Eric is alive but no yesterday's bid available (e.g., day 1 or prev trace error)
                # Default to a competitive bid against Eric based on meta-round context
                bid = DAILY_SALARY * 0.8 # 120
    
    # If Eric is not alive, or not the primary threat, consider other opponents
    elif yesterday_bids: # Only other opponents are alive
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.85: # Other opponents bid very high
            if my_hp > 3:
                bid = DAILY_SALARY * 0.6 # 90
            else:
                bid = max(DAILY_SALARY * 0.9, highest_prev_bid + 1) # 135, or slightly more
        elif highest_prev_bid > DAILY_SALARY * 0.5: # Other opponents bid moderately
            bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 2) # 75, or slightly more
        else: # Other opponents bid low
            bid = DAILY_SALARY * 0.4 # 60
            
    # Always cap bid by current budget
    final_bid = min(my_budget, bid)
    
    # Ensure bid is at least 1 to be considered a participant
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_players = len(alive_opponents) + 1

    # If I'm the only one left, bid minimally
    if num_alive_players == 1:
        return min(my_status['budget'], 1.0)

    # Collect yesterday's bids from all ALIVE opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid strategy, adjusted for my HP and competition.
    # Prioritize survival if HP is critical.
    if my_status['hp'] <= 2:
        # Very aggressive bid to survive
        return min(my_status['budget'], DAILY_SALARY * 0.98)

    # If HP is low but not critical, still be aggressive
    if my_status['hp'] <= 5:
        base_bid_for_hp = DAILY_SALARY * 0.90
    else:
        # Default for healthy HP
        base_bid_for_hp = DAILY_SALARY * 0.70

    bid_value = base_bid_for_hp

    # Adjust based on yesterday's highest bid
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        # If highest previous bid was very high, we need to be competitive.
        if max_yesterday_bid >= DAILY_SALARY * 0.85:
            # Bid slightly above it, but consider my current HP.
            if my_status['hp'] > 5: # Healthy, can be slightly less aggressive
                bid_value = max(base_bid_for_hp, max_yesterday_bid + 2.0)
            else: # Low HP, must be more aggressive
                bid_value = max(base_bid_for_hp, max_yesterday_bid + 5.0)
            # Cap at slightly above salary to avoid overspending drastically
            bid_value = min(bid_value, DAILY_SALARY * 1.05)
        else:
            # If previous bids were moderate or low, try to win without overspending.
            # Bid slightly above the max_yesterday_bid, but at least a decent percentage of salary.
            bid_value = max(base_bid_for_hp, max_yesterday_bid + 1.5)
            # Don't go too high if competition wasn't fierce
            bid_value = min(bid_value, DAILY_SALARY * 0.8)

    # Consider supply vs. demand as a final adjustment
    total_water_needed_by_alive = num_alive_players * WATER_REQ
    if day_context['supply'] < total_water_needed_by_alive: # Scarcity
        bid_value *= 1.1
    elif day_context['supply'] >= total_water_needed_by_alive + WATER_REQ: # Abundance
        bid_value *= 0.9

    # Final bid must not exceed budget
    final_bid = min(bid_value, my_status['budget'])

    # Ensure bid is always at least 1.0, unless budget doesn't allow.
    # If budget is less than 1.0, bid whatever is left.
    if final_bid < 1.0:
        final_bid = max(0.0, my_status['budget']) # Bid whatever is left, or 0 if budget is 0
    else:
        final_bid = max(1.0, final_bid) # Ensure it's at least 1.0 if it was >= 1.0 initially

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

    # Given supply 15-25 and WATER_REQ 13, only 1 agent can get water.
    # It's a winner-take-all scenario.

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to win
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Get the highest bid from yesterday among alive opponents
    highest_prev_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])

    # Base bid strategy
    current_bid = DAILY_SALARY * 0.7 # Start with a moderate bid

    # Adjust based on my HP
    if my_status['hp'] <= 2: # Critical HP, must win
        current_bid = DAILY_SALARY * 0.98 # Very aggressive
        if highest_prev_bid > 0:
            current_bid = max(current_bid, highest_prev_bid + 1.0)
    elif my_status['hp'] <= 4: # Low HP, need water soon
        current_bid = DAILY_SALARY * 0.9
        if highest_prev_bid > 0:
            current_bid = max(current_bid, highest_prev_bid + 1.0)
    else: # Healthy HP, can be strategic
        if highest_prev_bid > DAILY_SALARY * 0.8: # Opponents are bidding high
            current_bid = max(DAILY_SALARY * 0.85, highest_prev_bid + 1.0)
        else: # Opponents are not bidding very high, or no strong previous bid
            current_bid = DAILY_SALARY * 0.75 # Slightly higher than base to be competitive

    # Adjust based on remaining days
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] > 0: # End game, if I'm still alive, try to secure points
        current_bid = max(current_bid, DAILY_SALARY * 0.95) # Be more aggressive towards the end

    # Ensure bid does not exceed budget
    current_bid = min(current_bid, my_status['budget'])

    # Ensure bid is at least 1.0 (to participate)
    current_bid = max(1.0, current_bid)

    return current_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQUIREMENT = 13
    MY_DAILY_SALARY = 150
    EPISODE_DAYS = 10

    # Base bid: A reasonable amount to bid if no other information
    base_bid = MY_DAILY_SALARY * 0.7 

    # Adjust bid based on my current HP
    if my_status['hp'] <= 2:
        bid = MY_DAILY_SALARY * 0.95 # Very aggressive
    elif my_status['hp'] <= 4:
        bid = MY_DAILY_SALARY * 0.85 # Aggressive
    else:
        bid = base_bid # Default, moderate bid

    # Analyze opponents' previous bids to adjust my bid
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    highest_prev_bid = 0.0
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev_trace['bid'])

    # If opponents made significant bids yesterday, react to it
    if highest_prev_bid > 0:
        if my_status['hp'] <= 4: # I am desperate or need to secure water
            if highest_prev_bid >= MY_DAILY_SALARY * 0.8: # Opponents were very aggressive
                bid = max(bid, highest_prev_bid + 5.0) # Try to outbid
            elif highest_prev_bid >= MY_DAILY_SALARY * 0.5: # Opponents were moderately aggressive
                bid = max(bid, highest_prev_bid + 2.0) # Slightly outbid
            else: # Opponents were conservative, but I'm desperate
                bid = max(bid, MY_DAILY_SALARY * 0.6) # Ensure I bid enough
        else: # I have good HP, can be more strategic
            if highest_prev_bid >= MY_DAILY_SALARY * 0.8: # Opponents were very aggressive, but I'm not desperate
                bid = max(bid, highest_prev_bid * 0.9) # Bid slightly less, hope they overbid
            elif highest_prev_bid >= MY_DAILY_SALARY * 0.5: # Opponents were moderately aggressive
                bid = max(bid, highest_prev_bid + 1.0) # Slightly outbid
            else: # Opponents were conservative, I can bid low
                bid = min(bid, highest_prev_bid + 1.0) # Bid just above them
                if my_status['budget'] > MY_DAILY_SALARY * 2:
                    bid = max(bid, MY_DAILY_SALARY * 0.4) # Don't bid too low if I have plenty of budget

    # Consider end-game desperation
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] <= 5: # Last 2 days and low HP
        bid = MY_DAILY_SALARY * 0.98 # Maximize chances to survive

    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], bid)
    
    # Ensure bid is at least 1.0 to participate
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid calculation
    # Start with a default bid that's competitive but not overly aggressive
    my_bid_value = DAILY_SALARY * 0.65 # ~97.5

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP, need water desperately
        my_bid_value = DAILY_SALARY * 0.95 # Bid very high (~142.5)
    elif my_status['hp'] <= 4: # Low HP
        my_bid_value = DAILY_SALARY * 0.85 # High bid (~127.5)
    elif my_status['hp'] >= 8: # Healthy HP, can afford to be more conservative
        my_bid_value = DAILY_SALARY * 0.55 # Lower bid (~82.5)

    # Adjust bid based on supply scarcity
    supply = day_context['supply']
    # Calculate total water requirement for all active players (including myself)
    estimated_total_water_needed = WATER_REQ # For myself
    for opp in alive_opponents:
        estimated_total_water_needed += opp['water_requirement']

    # If supply is very tight (less than total estimated need)
    if supply < estimated_total_water_needed:
        # The more scarce, the more aggressive the bid
        scarcity_factor = estimated_total_water_needed / supply
        my_bid_value *= min(scarcity_factor * 1.1, 1.5) # Max 50% increase if very scarce
    # If supply is abundant (significantly more than total estimated need)
    elif supply > estimated_total_water_needed * 1.5:
        my_bid_value *= 0.8 # Decrease bid by 20%

    # Analyze yesterday's bids from opponents (previous_trace)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If the highest bid yesterday was already high, react to it
        # Especially if my bid is currently lower, or if I'm desperate
        if my_bid_value < highest_prev_bid + 5 and my_status['hp'] <= 5:
            # If my HP is low, ensure I'm competitive
            my_bid_value = max(my_bid_value, highest_prev_bid + 5)
        elif my_bid_value < highest_prev_bid + 1:
            # Otherwise, try to slightly outbid or match
            my_bid_value = max(my_bid_value, highest_prev_bid + 1)
        
        # If highest_prev_bid was very low (e.g., from Eric, Alex/Bob), don't overbid
        # But ensure my bid is still reasonable based on my HP and supply
        if highest_prev_bid < DAILY_SALARY * 0.4 and my_status['hp'] > 5:
            my_bid_value = min(my_bid_value, DAILY_SALARY * 0.6) # Don't bid too high if competition is weak

    # If no opponents, bid minimally to save budget
    if num_alive_opponents == 0:
        my_bid_value = DAILY_SALARY * 0.1 # Very low bid to save budget

    # Ensure bid is not negative or zero unless budget is zero
    final_bid = max(1.0, my_bid_value)
    # Never bid more than current budget
    final_bid = min(my_status['budget'], final_bid)
    # Cap bid at a reasonable maximum to prevent overspending even with high budget
    final_bid = min(final_bid, DAILY_SALARY * 1.5) # Max bid 1.5 times daily salary (225)

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

    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    # If supply is not enough for me, don't bid
    if current_supply < WATER_REQ:
        return 0.0

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to secure water
    if not alive_opponents:
        return min(my_budget, 1.0)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid
    base_bid = DAILY_SALARY * 0.5 # Default moderate bid

    # Aggressive bidding if HP is low or I missed water yesterday
    if my_hp <= 2 or my_no_water_days > 0:
        base_bid = DAILY_SALARY * 0.9
    elif my_hp <= 4: # Slightly less critical
        base_bid = DAILY_SALARY * 0.7

    # Adjust bid based on opponents' previous bids if available
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.75: # Opponent was very aggressive
            if my_hp <= 3: # Critical need for water
                base_bid = max(base_bid, highest_prev_bid + 5.0) # Try to outbid significantly
            else: # Healthy, but need to compete
                base_bid = max(base_bid, highest_prev_bid + 1.0) # Slightly outbid
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Opponent was moderately aggressive
            base_bid = max(base_bid, highest_prev_bid + 1.0) # Try to slightly outbid
        else: # Opponents were bidding low
            base_bid = max(base_bid, highest_prev_bid + 0.5) # Bid slightly above to win cheaply

    # Final bid must be capped by budget
    final_bid = min(my_budget, base_bid)

    # Ensure bid is at least 0.0, or 1.0 if water is critically needed and budget allows
    if final_bid <= 0.0 and my_budget > 0.0 and current_supply >= WATER_REQ and (my_hp <= 2 or my_no_water_days > 0):
        final_bid = min(my_budget, 1.0)
    elif final_bid < 0.0:
        final_bid = 0.0

    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    current_day = day_context['day']
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid calculation
    base_bid = DAILY_SALARY * 0.5

    # Adjust bid based on my HP and no_water_days (urgency)
    if my_hp <= 2 or my_no_water_days >= 1: # Critical condition
        base_bid = DAILY_SALARY * 0.9
    elif my_hp <= 5: # Low HP, but not critical
        base_bid = DAILY_SALARY * 0.7

    # Adjust bid based on supply and competition
    available_water_slots = int(supply // WATER_REQ)

    if num_alive_opponents == 0:
        # If I am the only one, bid minimally unless desperate
        if my_hp <= 2 or my_no_water_days >= 1:
            base_bid = max(base_bid, DAILY_SALARY * 0.5) # Still higher if desperate
        else:
            base_bid = min(base_bid, DAILY_SALARY * 0.2) # Bid low if no competition
    else:
        # If supply is very low (less than my requirement), bid very high
        if supply < WATER_REQ:
            base_bid = DAILY_SALARY * 0.95 # Desperate bid
        # If competition is high (fewer slots than active bidders)
        elif available_water_slots <= (num_alive_opponents + 1): # +1 for me
            # If there are fewer slots than people, competition is fierce
            if current_day < EPISODE_DAYS: # Not the last day, still some budget management
                base_bid = max(base_bid, DAILY_SALARY * 0.75)
            else: # Last day, go all in if needed
                base_bid = max(base_bid, DAILY_SALARY * 0.9)
        # If supply is abundant (many more slots than active bidders)
        elif available_water_slots > (num_alive_opponents + 1) * 1.5: # Abundant supply
            base_bid = min(base_bid, DAILY_SALARY * 0.3)
        elif available_water_slots > (num_alive_opponents + 1): # Moderate abundance
            base_bid = min(base_bid, DAILY_SALARY * 0.4)

    # React to yesterday's opponent bids from their 'previous_trace'
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace')
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)
        max_yesterday_bid = max(yesterday_bids)

        # If opponents were aggressive yesterday
        if max_yesterday_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, max_yesterday_bid + 5) # Bid slightly higher than max
        elif avg_yesterday_bid >= DAILY_SALARY * 0.6:
            base_bid = max(base_bid, avg_yesterday_bid + 2) # Bid slightly higher than avg
        # If opponents were conservative yesterday
        elif avg_yesterday_bid < DAILY_SALARY * 0.3:
            # Only lower bid if I'm not in critical condition
            if my_hp > 5 and my_no_water_days == 0:
                base_bid = min(base_bid, avg_yesterday_bid * 0.9)

    # Final bid constraints
    final_bid = min(my_budget, base_bid)
    final_bid = max(1.0, final_bid) # Ensure bid is at least 1

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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Default bid if no strong reason to change
    base_bid = DAILY_SALARY * 0.5

    # 1. Look at yesterday's situation (Trace)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Strategy adjustments:

    # If no opponents, bid minimally to save budget, but still secure water if needed
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1 if my_hp >= 10 else DAILY_SALARY * 0.3)

    # Critical HP: Bid very aggressively to survive
    if my_hp <= 2:
        return min(my_budget, DAILY_SALARY * 0.95)
    # Low HP: Still aggressive
    elif my_hp <= 5:
        base_bid = DAILY_SALARY * 0.85
        # If there were high bids yesterday, try to beat them
        if highest_prev_bid > base_bid * 0.8:
            base_bid = max(base_bid, highest_prev_bid + 5)
    # Healthy HP
    else:
        # If previous bids were high, we might need to match or slightly exceed to stay competitive
        if highest_prev_bid >= DAILY_SALARY * 0.7:
            base_bid = max(base_bid, highest_prev_bid + 2)
        elif highest_prev_bid > 0:
            base_bid = max(base_bid, highest_prev_bid * 1.05)
        else:
            base_bid = DAILY_SALARY * 0.45 # Conservative bid

    # End-game pressure:
    days_left = EPISODE_DAYS - current_day
    if days_left <= 2: # Last 2 days
        if my_hp <= 7: # Need to survive
            base_bid = max(base_bid, DAILY_SALARY * 0.9)
        else: # Healthy, but still need to win to finish strong
            base_bid = max(base_bid, highest_prev_bid + 10 if highest_prev_bid > 0 else DAILY_SALARY * 0.7)
    elif days_left <= 4: # Mid-late game
        if my_hp <= 5:
            base_bid = max(base_bid, DAILY_SALARY * 0.8)

    # Ensure bid is positive and within budget
    final_bid = min(my_budget, base_bid)
    return max(0.0, final_bid)
"""
