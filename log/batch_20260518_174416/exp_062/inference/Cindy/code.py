# ============================================================
# Experiment: exp_062
# Agent: Cindy
# Source: exp_062
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    supply = day_context['supply']
    day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid strategy
    # Default to a moderate bid
    bid_amount = DAILY_SALARY * 0.5

    # 1. Survival strategy (if my HP is critical)
    if my_status['hp'] <= 2:
        bid_amount = DAILY_SALARY * 0.95
    elif my_status['no_water_days'] >= 1: # Didn't get water yesterday, need to prioritize
        bid_amount = DAILY_SALARY * 0.75
    elif my_status['hp'] <= 4: # Warning HP
        bid_amount = DAILY_SALARY * 0.65
    else: # Healthy HP, try to conserve
        bid_amount = DAILY_SALARY * 0.45

    # 2. React to opponent's previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were very aggressive yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] <= 3: # If I also need water, outbid them
                bid_amount = max(bid_amount, highest_prev_bid + 5)
            else: # If healthy, maybe don't engage in a bidding war unless supply is abundant
                available_water_slots = int(supply // WATER_REQ)
                if num_alive_opponents + 1 > available_water_slots: # High competition
                    bid_amount = max(bid_amount, DAILY_SALARY * 0.7) # Still need to be competitive
                else: # Enough water, maybe try to conserve
                    bid_amount = min(bid_amount, highest_prev_bid * 0.9) # Try to get cheaper
                    if bid_amount < DAILY_SALARY * 0.4: bid_amount = DAILY_SALARY * 0.4
        # If opponents were moderately competitive
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            if my_status['hp'] <= 4: # If I need water or am slightly low, bid competitively
                bid_amount = max(bid_amount, highest_prev_bid + 2)
            else: # Healthy, try to get it slightly cheaper but still above
                bid_amount = max(bid_amount, highest_prev_bid * 0.95)
        # If opponents bid low yesterday
        else:
            # Bid slightly above the highest low bid to secure water cheaply
            bid_amount = max(bid_amount, highest_prev_bid + 1)
            # Ensure it's not too low if I need water
            if my_status['hp'] <= 3:
                bid_amount = max(bid_amount, DAILY_SALARY * 0.6)

    # 3. Adjust for supply and number of competitors
    available_water_slots = int(supply // WATER_REQ)
    if num_alive_opponents + 1 > available_water_slots: # More agents than full water slots
        # High competition expected, increase bid if not already high
        if my_status['hp'] <= 4:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.7)
        else:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.55) # Stay competitive but conserve
    else: # Enough water for everyone, try to get it cheaper
        if my_status['hp'] > 4:
            bid_amount = min(bid_amount, DAILY_SALARY * 0.4) # Conserve if healthy and low competition

    # 4. End-game strategy
    remaining_days = EPISODE_DAYS - day
    if remaining_days <= 2:
        if my_status['hp'] <= 3: # Critical HP in end game, go all in
            bid_amount = DAILY_SALARY * 0.99
        else: # Healthy in end game, might as well spend more to secure win
            bid_amount = max(bid_amount, DAILY_SALARY * 0.7)

    # Final bid cannot exceed budget, and must be at least 1
    final_bid = min(my_status['budget'], bid_amount)
    final_bid = max(final_bid, 1.0) # Ensure it's at least 1, and float

    return round(final_bid, 2)
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
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            else:
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else:
            base_bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)
            if my_status['no_water_days'] > 0:
                base_bid = max(base_bid, DAILY_SALARY * 0.7)
            return min(my_status['budget'], base_bid)

    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    elif my_status['no_water_days'] > 0:
        return min(my_status['budget'], DAILY_SALARY * 0.7)
    else:
        return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    current_day = day_context['day']
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Calculate total water needed by all alive agents (including myself)
    total_water_needed = WATER_REQ
    for opp in alive_opponents:
        total_water_needed += opp['water_requirement']

    # Determine if supply is scarce
    is_supply_scarce = supply < total_water_needed

    # Base bid amount
    bid_amount = DAILY_SALARY * 0.5 # Default: 75

    # 1. Adapt bid based on desperation (HP and no_water_days)
    if my_hp <= 2 or my_no_water_days > 0:
        # Highly desperate, bid aggressively to survive
        bid_amount = DAILY_SALARY * 0.95 # 142.5
    elif my_hp <= 4:
        # Moderately desperate
        bid_amount = DAILY_SALARY * 0.8 # 120
    elif my_hp > 7 and my_budget > DAILY_SALARY * 1.5: # Healthy and good budget
        # Can afford to be more conservative
        bid_amount = DAILY_SALARY * 0.4 # 60

    # 2. Adjust bid based on opponent's yesterday's bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents were very aggressive
            if my_hp > 5 and not is_supply_scarce: # Can afford to be slightly less aggressive
                bid_amount = min(bid_amount, DAILY_SALARY * 0.6) # Try to save
            else: # Must compete
                bid_amount = max(bid_amount, highest_prev_bid + 2.0) # Bid slightly higher
        else: # Opponents were moderate
            if is_supply_scarce: # Compete more if supply is tight
                bid_amount = max(bid_amount, highest_prev_bid + 1.5)
            else: # Supply is abundant, try to save
                bid_amount = min(bid_amount, highest_prev_bid + 1.0)

    # 3. Adjust for number of opponents and supply
    if num_alive_opponents == 0:
        bid_amount = DAILY_SALARY * 0.1 # No competition, bid very low
    elif is_supply_scarce:
        # Increase bid if supply is tight, unless already very desperate
        if my_hp > 5: # Only if not already desperate
            bid_amount = max(bid_amount, DAILY_SALARY * 0.7) # 105

    # 4. End-game aggression
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2:
        # Be more aggressive towards the end if survival is key
        if my_hp <= 5 or is_supply_scarce:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.9) # 135

    # Ensure bid is at least a minimal amount if there's competition
    if num_alive_opponents > 0 and bid_amount < DAILY_SALARY * 0.2:
        bid_amount = DAILY_SALARY * 0.2 # Minimum competitive bid

    # Critical: Cap the bid by current budget, as per example provided in prompt
    # If budget is very low, but I'm desperate, I have to bid all of it.
    if my_budget <= 0:
        final_bid = 0.0 # Cannot bid if budget is 0 or negative
    elif my_budget < bid_amount and (my_hp <= 3 or my_no_water_days > 0): # Desperate and budget is less than calculated bid
        final_bid = my_budget # Bid all available budget to survive
    else:
        final_bid = min(my_budget, bid_amount) # Otherwise, cap normally

    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    min_survival_bid = DAILY_SALARY * 0.3 
    moderate_bid = DAILY_SALARY * 0.6 
    high_pressure_bid = DAILY_SALARY * 0.8 
    critical_hp_bid = DAILY_SALARY * 0.95 

    if num_alive_opponents == 0:
        return min(my_budget, min_survival_bid)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_previous_bid = 0
    if yesterday_bids:
        max_previous_bid = max(yesterday_bids)

    bid_value = 0

    if my_hp <= 2 or my_no_water_days > 0:
        bid_value = critical_hp_bid
        if max_previous_bid > 0:
            bid_value = max(bid_value, max_previous_bid + 5)

    elif my_hp <= 4:
        bid_value = high_pressure_bid
        if max_previous_bid > 0:
            bid_value = max(bid_value, max_previous_bid + 2)

    else:
        if max_previous_bid > 0:
            if max_previous_bid >= moderate_bid:
                bid_value = max(moderate_bid, max_previous_bid + 1)
            else:
                bid_value = moderate_bid
        else:
            bid_value = moderate_bid

    bid_value = min(bid_value, DAILY_SALARY)
    bid_value = min(bid_value, my_budget)

    if bid_value <= 0 and my_budget > 0:
        bid_value = min(my_budget, 1.0)

    return bid_value
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
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 5:
                return min(my_status['budget'], DAILY_SALARY * 0.35)
            elif my_status['hp'] > 2:
                return min(my_status['budget'], DAILY_SALARY * 0.9)
            else:
                return min(my_status['budget'], DAILY_SALARY * 0.98)
        else:
            bid_amount = max(DAILY_SALARY * 0.5, highest_prev_bid + 2.0)
            return min(my_status['budget'], bid_amount)

    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 5:
        return min(my_status['budget'], DAILY_SALARY * 0.7)
    else:
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
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_prev_bid = 0
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)

    current_bid = 0

    # Strategy based on HP and competition for the single water slot
    if my_status['hp'] <= 3:  # Critical HP, must win
        # Bid very aggressively, significantly above previous max, up to budget
        current_bid = max(DAILY_SALARY * 1.15, max_prev_bid + 15)
    elif my_status['hp'] <= 5:  # Low HP, strong need to win
        # Bid aggressively, above previous max, up to salary
        current_bid = max(DAILY_SALARY * 1.05, max_prev_bid + 10)
    else:  # Healthy HP, try to be competitive but save money
        # Adjust aggressiveness based on number of active opponents
        if num_alive_opponents >= 3:
            # Many opponents, bid competitively
            current_bid = max(DAILY_SALARY * 0.95, max_prev_bid + 5)
        elif num_alive_opponents == 2:
            # Fewer opponents, can be slightly less aggressive
            current_bid = max(DAILY_SALARY * 0.9, max_prev_bid + 3)
        else: # Only one opponent left
            # Try to outbid them directly but don't overspend if not necessary
            current_bid = max(DAILY_SALARY * 0.85, max_prev_bid + 1)

    # If the calculated bid is too low (e.g., no high previous bids), set a floor
    if current_bid < DAILY_SALARY * 0.8:
        current_bid = DAILY_SALARY * 0.8

    # Ensure bid does not exceed current budget
    current_bid = min(current_bid, my_status['budget'])

    # Ensure bid is at least 1
    current_bid = max(1, current_bid)

    return current_bid
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

    # CRITICAL HEALTH: If HP is very low, bid aggressively to survive
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    # If I haven't received water recently, I need to increase my chances
    if my_status['no_water_days'] > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.8: # If opponents are very aggressive
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        elif highest_prev_bid > 0:
            return min(my_status['budget'], highest_prev_bid + 2.0)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.75)

    current_supply = day_context['supply']

    # If supply is very tight (only enough for one full requirement or slightly more)
    if current_supply <= WATER_REQ + 4: # Covers supply 15-17 for WATER_REQ=13
        if my_status['hp'] <= 4: # Moderate health concern, be more aggressive
            return min(my_status['budget'], DAILY_SALARY * 0.8)
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            return min(my_status['budget'], highest_prev_bid + 1.5)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.7)

    # General bidding based on opponent pressure and my health
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if my_status['hp'] > 3:
            return min(my_status['budget'], DAILY_SALARY * 0.6)
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    
    elif highest_prev_bid >= DAILY_SALARY * 0.6:
        return min(my_status['budget'], highest_prev_bid + 1.0)

    # Default bid: No strong pressure from opponents or my health
    if day_context['day'] >= EPISODE_DAYS - 2:
        return min(my_status['budget'], DAILY_SALARY * 0.7)
    else:
        return min(my_status['budget'], DAILY_SALARY * 0.55)
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
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.2)

    # --- Collect yesterday's bids from alive opponents ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # --- Base bid calculation ---
    # Start with a default bid, slightly below daily salary to save budget
    base_bid = DAILY_SALARY * 0.65 

    # --- Adjust for my desperation ---
    # If HP is critical, bid very high
    if my_hp <= 2:
        return min(my_budget, DAILY_SALARY * 1.2 + (EPISODE_DAYS - current_day) * 5)
    # If I haven't gotten water recently and HP is low
    if my_no_water_days >= 1 and my_hp <= 4:
        return min(my_budget, DAILY_SALARY * 1.1 + my_no_water_days * 10)
    # If I haven't gotten water recently but HP is okay
    elif my_no_water_days >= 1:
        base_bid = max(base_bid, DAILY_SALARY * 0.9 + my_no_water_days * 5)

    # --- Adjust based on opponent's previous bids ---
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were very aggressive last round
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            # If my HP is good, try to outbid but don't overspend too much
            if my_hp > 5:
                base_bid = max(base_bid, highest_prev_bid + 2)
            else: # If my HP is moderate/low, I need to be more aggressive
                base_bid = max(base_bid, highest_prev_bid + 5)
        # If opponents were somewhat competitive
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            base_bid = max(base_bid, highest_prev_bid + 1)
        # If opponents were bidding low, try to win cheaply
        else:
            base_bid = max(base_bid, highest_prev_bid + 0.5) # Bid slightly above to ensure win

    # --- Adjust for supply scarcity ---
    # If supply is tight (less than 1.5x my requirement per agent), increase bid
    if current_supply < WATER_REQ * 1.5 * (len(alive_opponents) + 1):
        base_bid += DAILY_SALARY * 0.1
    # If supply is very abundant, consider bidding lower
    elif current_supply >= WATER_REQ * 2 * (len(alive_opponents) + 1):
        base_bid -= DAILY_SALARY * 0.05
    
    # --- Adjust for late game pressure ---
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        base_bid += DAILY_SALARY * 0.15
    elif current_day >= EPISODE_DAYS - 4: # Last 4 days
        base_bid += DAILY_SALARY * 0.05

    # Final bid must be within budget and non-negative
    final_bid = min(my_budget, base_bid)
    final_bid = max(0.0, final_bid)

    # Ensure a minimum bid to stay competitive if not desperate
    if final_bid < DAILY_SALARY * 0.2 and my_hp > 2:
        final_bid = max(final_bid, DAILY_SALARY * 0.2)

    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    # The scenario has 10 episode days, hardcoding for clarity, but could be dynamic if provided in day_context
    EPISODE_DAYS = 10 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid a minimal amount to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # Initialize target bid based on HP
    if my_status['hp'] <= 2: # Critically low HP, must win
        target_bid = DAILY_SALARY * 1.2 # Bid very aggressively (180)
    elif my_status['hp'] <= 4: # Low HP, need water
        target_bid = DAILY_SALARY * 1.1 # Bid aggressively (165)
    else: # Normal HP, can be more strategic
        target_bid = DAILY_SALARY * 0.7 # Base bid (105)

    # Adjust bid based on yesterday's highest bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If I am not critically low on HP, and the highest bid was very high (likely Eric)
        # I might choose to conserve budget if my HP is good and it's not the very end.
        if my_status['hp'] > 4 and highest_prev_bid > DAILY_SALARY * 1.0: # If Eric likely bid very high (e.g., > 150)
            # If I have a good HP buffer and it's not near the end of the meta-round
            if my_status['hp'] > 6 and day_context['day'] < EPISODE_DAYS - 2: 
                # Conserve budget, bid moderately and potentially lose this round
                target_bid = min(target_bid, DAILY_SALARY * 0.8) 
            else: 
                # HP buffer not huge or near end, still try to compete with Eric
                target_bid = max(target_bid, highest_prev_bid + 5) 
        else:
            # Otherwise, try to outbid previous highest bid or maintain current target
            target_bid = max(target_bid, highest_prev_bid + 1)
            
    # Further adjustments for late game
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days
        target_bid = max(target_bid, DAILY_SALARY * 1.15) # Be very aggressive
    elif day_context['day'] >= EPISODE_DAYS - 4: # Last 4 days
        target_bid = max(target_bid, DAILY_SALARY * 1.0) # Be aggressive

    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], target_bid)

    # Ensure bid is at least 1 if budget allows, to avoid 0 bids unless no budget
    if final_bid == 0 and my_status['budget'] > 0:
        return 1.0
    
    # Ensure bid is not negative (though min(budget, target_bid) should handle this)
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

    bid_percentage = 0.55

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    if my_status['hp'] <= 2:
        bid_percentage = 0.95
    elif my_status['no_water_days'] > 0:
        bid_percentage = 0.8

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.8:
            bid_percentage = max(bid_percentage, 0.90)
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            bid_percentage = max(bid_percentage, 0.75)

    current_supply = day_context['supply']
    num_slots = int(current_supply // WATER_REQ)

    if num_slots == 0:
        bid_percentage = 0.99
    elif num_slots == 1:
        bid_percentage = max(bid_percentage, 0.90)
        if yesterday_bids and bid_percentage < 0.95:
            bid_val_from_opp = highest_prev_bid * 1.05
            if (bid_val_from_opp / DAILY_SALARY) > bid_percentage:
                bid_percentage = min(0.95, bid_val_from_opp / DAILY_SALARY)
    elif num_slots >= len(alive_opponents) + 1:
        bid_percentage = min(bid_percentage, 0.4)
        if yesterday_bids:
            bid_percentage = min(bid_percentage, (avg_prev_bid / DAILY_SALARY) * 0.9)
    elif num_slots > 1 and num_slots < len(alive_opponents) + 1:
        if yesterday_bids:
            bid_percentage = max(bid_percentage, (avg_prev_bid / DAILY_SALARY) * 1.1)
            bid_percentage = min(bid_percentage, 0.8)

    final_bid = DAILY_SALARY * bid_percentage

    final_bid = min(my_status['budget'], final_bid)

    final_bid = max(1.0, final_bid)

    return final_bid
"""
