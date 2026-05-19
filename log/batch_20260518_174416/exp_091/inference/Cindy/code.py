# ============================================================
# Experiment: exp_091
# Agent: Cindy
# Source: exp_091
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
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_budget, 1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        # Ensure it's yesterday's trace and a bid was made
        if prev_trace and prev_trace.get('day') == current_day - 1 and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # --- Determine bid strategy based on HP and opponent history ---
    bid_amount = 0.0

    # 1. Critical HP: Always bid very high to survive
    if my_hp <= 2:
        bid_amount = DAILY_SALARY * 0.95
    # 2. Low HP: Bid high to secure water
    elif my_hp <= 4:
        bid_amount = DAILY_SALARY * 0.75
    # 3. Moderate to High HP: Adjust based on opponent's previous bids
    else:
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            # If opponents were very aggressive yesterday, be competitive
            if highest_prev_bid >= DAILY_SALARY * 0.8:
                bid_amount = highest_prev_bid + 1.0 # Bid slightly above to win
            # If moderately aggressive
            elif highest_prev_bid >= DAILY_SALARY * 0.5:
                bid_amount = highest_prev_bid + 1.0 # Try to win by slightly outbidding
            # If not very aggressive, try to save money but still win
            else:
                bid_amount = highest_prev_bid + 1.0
                # Ensure a minimum bid even if previous bids were very low, to stay competitive
                bid_amount = max(bid_amount, DAILY_SALARY * 0.4)
        else: # Day 1 or no opponent history for healthy HP
            bid_amount = DAILY_SALARY * 0.55 # Start moderately competitive

    # Ensure the bid does not exceed available budget and is at least 0
    final_bid = min(my_budget, bid_amount)
    return max(0, final_bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 
    MIN_SUPPLY = 15 
    MAX_SUPPLY = 25 
    MAX_HP = 10 

    current_day = day_context['day']
    supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid calculation
    base_bid = DAILY_SALARY * 0.6 

    # Adjust bid based on my HP
    if my_status['hp'] <= 3:
        base_bid = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 5:
        base_bid = DAILY_SALARY * 0.75
    elif my_status['hp'] >= 8 and current_day > EPISODE_DAYS / 2: 
        base_bid = DAILY_SALARY * 0.5
    
    # Adjust bid based on no_water_days (critical)
    if my_status['no_water_days'] >= 1:
        base_bid = DAILY_SALARY * 0.95 
    
    # Adjust bid based on remaining days and budget
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: 
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    
    # Analyze opponents' previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    # Adjust bid based on max_yesterday_bid
    if max_yesterday_bid > DAILY_SALARY * 0.6: 
        if my_status['hp'] <= 5 or my_status['no_water_days'] >= 1:
            base_bid = max(base_bid, max_yesterday_bid + 5) 
        else:
            base_bid = max(base_bid, max_yesterday_bid * 0.9) 
    elif max_yesterday_bid > 0: 
        base_bid = max(base_bid, max_yesterday_bid + 1) 

    # Adjust bid based on supply relative to total water requirement
    total_water_needed = WATER_REQ + sum(o['water_requirement'] for o in alive_opponents)
    
    if supply < total_water_needed:
        supply_ratio = supply / total_water_needed if total_water_needed > 0 else 1
        if supply_ratio < 0.75: 
            base_bid = max(base_bid, DAILY_SALARY * 0.8)
        if supply_ratio < 0.5: 
            base_bid = max(base_bid, DAILY_SALARY * 0.9)
    
    # Final bid should not exceed budget and should be positive
    final_bid = min(my_status['budget'], base_bid)
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

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    num_available_water_units = int(current_supply / WATER_REQ)

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.3)

    yesterday_bids = []
    strong_opponents_yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            # Assuming Alex has similar profile (water_requirement, daily_salary)
            if opp['water_requirement'] == WATER_REQ and opp['daily_salary'] == DAILY_SALARY:
                strong_opponents_yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.8 # Default starting bid (120)

    if strong_opponents_yesterday_bids:
        highest_strong_bid = max(strong_opponents_yesterday_bids)
        if highest_strong_bid >= DAILY_SALARY * 1.1:
            base_bid = highest_strong_bid + 5
        elif highest_strong_bid >= DAILY_SALARY * 0.9:
            base_bid = highest_strong_bid + 2
        else:
            base_bid = max(base_bid, highest_strong_bid + 1)
    elif yesterday_bids:
        highest_yesterday_bid = max(yesterday_bids)
        base_bid = max(base_bid, highest_yesterday_bid + 1)
        base_bid = min(base_bid, DAILY_SALARY * 0.7) # Cap for weak competition

    if my_hp <= 3:
        base_bid = max(base_bid, DAILY_SALARY * 1.15)
    elif my_no_water_days >= 1:
        base_bid = max(base_bid, DAILY_SALARY * 1.05)
    elif my_hp >= EPISODE_DAYS * 0.9 and current_day < EPISODE_DAYS / 2:
        base_bid = min(base_bid, DAILY_SALARY * 0.7)

    final_bid = min(my_budget, base_bid)

    if current_day >= EPISODE_DAYS - 2 and my_hp > 0:
        remaining_days = EPISODE_DAYS - current_day + 1
        required_budget_per_day = my_budget / remaining_days
        if required_budget_per_day >= DAILY_SALARY * 1.0:
            final_bid = max(final_bid, DAILY_SALARY * 1.1)
        else:
            final_bid = max(final_bid, DAILY_SALARY * 0.9)
        final_bid = min(my_budget, final_bid)

    if final_bid < 0.1 and my_budget > 0:
        final_bid = min(my_budget, DAILY_SALARY * 0.1)

    if num_available_water_units == 1 and alive_opponents and my_no_water_days >= 1:
        final_bid = max(final_bid, DAILY_SALARY * 1.1)
        final_bid = min(my_budget, final_bid)

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
    num_alive_opponents = len(alive_opponents)

    # Base bid calculation
    # Start with a moderate bid, assuming I want water but don't want to overpay
    base_bid = DAILY_SALARY * 0.65

    # --- Adjust bid based on my HP ---
    # If HP is critical, bid very aggressively
    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.95
    # If HP is low, bid aggressively
    elif my_status['hp'] <= 5:
        base_bid = DAILY_SALARY * 0.85
    # If HP is very high and I can afford to miss a day (e.g., HP > remaining days), be slightly more conservative
    elif my_status['hp'] > (EPISODE_DAYS - day_context['day']):
        base_bid = DAILY_SALARY * 0.6

    # --- Adjust bid based on opponent's previous activity (yesterday's bids) ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest bid was already very high, I might need to slightly exceed it
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            # If my HP is low, I MUST outbid
            if my_status['hp'] <= 5:
                base_bid = max(base_bid, highest_prev_bid + 5)
            # If my HP is healthy, I can try to outbid but not necessarily go crazy
            else:
                base_bid = max(base_bid, highest_prev_bid + 1)
        # If highest bid was low, I can try to get it cheaper, but still ensure I get water
        elif highest_prev_bid < DAILY_SALARY * 0.5:
            base_bid = min(base_bid, highest_prev_bid + 10)
        else: # Moderate previous bids
            base_bid = max(base_bid, highest_prev_bid + 2)

    # --- Adjust bid based on current supply and number of competitors ---
    # If supply is very tight (e.g., just enough for me + a few others), competition will be fierce
    if day_context['supply'] <= WATER_REQ + num_alive_opponents * 2:
        base_bid *= 1.1 # Increase bid by 10%
    # If supply is abundant, I can try to get it cheaper
    elif day_context['supply'] >= WATER_REQ * 2:
        base_bid *= 0.9 # Decrease bid by 10%

    # --- Adjust bid for late game ---
    # In the last few days, survival is paramount, so bid aggressively
    if day_context['day'] >= EPISODE_DAYS - 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)

    # --- Final bid adjustments ---
    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure bid is at least 1.0 to participate, and not negative
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_BID = 1

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return max(MIN_BID, min(my_status['budget'], DAILY_SALARY * 0.1))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_day = day_context['day']
    supply = day_context['supply']
    
    base_bid_value = DAILY_SALARY * 0.55

    if supply < 18:
        base_bid_value = DAILY_SALARY * 0.7
    elif supply > 22:
        base_bid_value = DAILY_SALARY * 0.4
    
    if current_day >= 8:
        base_bid_value *= 1.15
    elif current_day <= 2:
        base_bid_value *= 0.9

    bid = base_bid_value

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 8:
                bid = DAILY_SALARY * 0.35
            else:
                bid = DAILY_SALARY * 0.95
        else:
            bid = max(base_bid_value, highest_prev_bid + 5)
            
            if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
                bid = max(bid, DAILY_SALARY * 0.9)

    else:
        if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
            bid = DAILY_SALARY * 0.9
        else:
            bid = base_bid_value

    bid = min(my_status['budget'], bid)
    return max(MIN_BID, bid)
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

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.5 # Default moderate bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        lowest_prev_bid = min(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            base_bid = max(base_bid, highest_prev_bid + 2)
        else:
            base_bid = max(base_bid, lowest_prev_bid + 1)

    if my_status['hp'] <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 5:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] < WATER_REQ * 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif remaining_days <= 4 and my_status['hp'] < WATER_REQ * 3:
        base_bid = max(base_bid, DAILY_SALARY * 0.7)

    num_agents_needing_water = 1
    for opp in alive_opponents:
        if opp['hp'] < WATER_REQ * 2:
            num_agents_needing_water += 1

    if day_context['supply'] < WATER_REQ * num_agents_needing_water:
        base_bid = base_bid * 1.1
        if my_status['hp'] <= 5:
            base_bid = base_bid * 1.15
    elif day_context['supply'] >= WATER_REQ * (1 + len(alive_opponents)) * 1.5:
        base_bid = base_bid * 0.9

    final_bid = min(my_status['budget'], base_bid)

    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    my_current_bid = DAILY_SALARY * 0.5 # Start with a moderate bid

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid just enough to survive cheaply
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1) # Bid very low if no competition

    # Calculate total water demand and supply ratio
    total_opponent_water_req = sum(o['water_requirement'] for o in alive_opponents)
    total_demand = WATER_REQ + total_opponent_water_req
    
    supply = day_context['supply']
    
    # Adjust bid based on supply scarcity
    if supply < total_demand:
        # Supply is scarce, increase bid
        scarcity_factor = (total_demand / supply) # e.g., if demand is 2x supply, factor is 2
        my_current_bid *= min(scarcity_factor, 1.5) # Cap scarcity factor to avoid absurd bids
    elif supply > total_demand * 1.5:
        # Supply is abundant, decrease bid
        my_current_bid *= 0.8
    
    # Analyze yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If previous bids were high, we might need to match or exceed
        if highest_prev_bid > DAILY_SALARY * 0.7:
            my_current_bid = max(my_current_bid, highest_prev_bid * 1.05) # Try to outbid
        elif highest_prev_bid > DAILY_SALARY * 0.5:
            my_current_bid = max(my_current_bid, highest_prev_bid * 0.9) # Stay competitive
        else:
            # If bids were low, try to bid slightly above average or keep base bid
            my_current_bid = max(my_current_bid, average_prev_bid * 1.1)

    # Adjust bid based on my HP (prioritize survival)
    if my_status['hp'] <= 2: # Critical HP
        my_current_bid = max(my_current_bid, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4: # Low HP
        my_current_bid = max(my_current_bid, DAILY_SALARY * 0.8)
    elif my_status['hp'] <= 6: # Moderate HP
        my_current_bid = max(my_current_bid, DAILY_SALARY * 0.65)
    
    # Adjust bid based on day (late game aggression)
    if day_context['day'] >= EPISODE_DAYS * 0.7 and my_status['hp'] > 0: # Last few days
        if my_status['hp'] > 5: # If healthy, push harder
            my_current_bid = max(my_current_bid, DAILY_SALARY * 0.75)
        else: # If struggling, still prioritize survival
            my_current_bid = max(my_current_bid, DAILY_SALARY * 0.9)

    # Ensure bid doesn't go below a sensible minimum
    my_current_bid = max(my_current_bid, DAILY_SALARY * 0.1) 
    
    # Final check: Don't bid more than budget
    return min(my_status['budget'], my_current_bid)
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
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    eric_status = opponents_status.get('Eric')
    eric_previous_bid = 0
    if eric_status and eric_status['alive']:
        prev_trace = eric_status.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            eric_previous_bid = prev_trace['bid']

    base_bid = DAILY_SALARY * 0.6 # Default moderate bid
    
    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.8
    
    # Adjust bid based on day (more aggressive towards end if budget allows)
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 3 and my_status['hp'] <= 5: # Late game, low HP
        base_bid = max(base_bid, DAILY_SALARY * 1.0) # Bid full salary or more

    # Adjust bid based on supply (higher bid if supply is scarce)
    if day_context['supply'] < WATER_REQ * 1.5: # If supply is less than 1.5x my requirement, it's competitive
        base_bid = max(base_bid, DAILY_SALARY * 0.75)
    
    # React to Eric's previous bid
    if eric_previous_bid > 0:
        if eric_previous_bid >= DAILY_SALARY * 0.8: # Eric bid high
            base_bid = max(base_bid, eric_previous_bid + 5.0) # Try to outbid him
        elif eric_previous_bid >= DAILY_SALARY * 0.5: # Eric bid moderately
            base_bid = max(base_bid, eric_previous_bid + 2.0) # Try to outbid him slightly
        else: # Eric bid low, maybe conserve or he didn't need water. Be careful.
            base_bid = max(base_bid, DAILY_SALARY * 0.65) # Don't go too low just because he did.

    # Ensure bid does not exceed budget and is not negative
    final_bid = min(my_status['budget'], base_bid)
    final_bid = max(0.0, final_bid)

    # If HP is very critical, bid almost everything
    if my_status['hp'] <= 1:
        final_bid = min(my_status['budget'], DAILY_SALARY * 1.1) # Bid slightly more than salary if desperate
        final_bid = max(0.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # 1. If I'm the only one left, bid minimally
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # 2. Aggressive bidding if HP is critically low or I missed water yesterday
    if my_status['hp'] <= 1 or my_status['no_water_days'] > 0:
        # Bid very aggressively to survive, aiming to outbid even Eric's max bids
        return min(my_status['budget'], DAILY_SALARY * 1.6) # 1.6 * 150 = 240

    # 3. Analyze opponent's previous bids, prioritizing Eric's behavior
    highest_prev_bid = 0.0
    eric_was_alive_yesterday = False
    eric_prev_bid = 0.0

    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                if prev['bid'] > highest_prev_bid:
                    highest_prev_bid = prev['bid']
                if opp_id == "Eric":
                    eric_prev_bid = prev['bid']
                    eric_was_alive_yesterday = True

    current_supply = day_context['supply']
    bid = DAILY_SALARY * 0.6 # Default moderate bid

    # Adjust bid based on supply and opponent behavior
    # If supply is very tight (e.g., barely enough for me and one more player)
    if current_supply < WATER_REQ * 1.5 and num_alive_opponents >= 1: 
        if eric_was_alive_yesterday and eric_prev_bid > DAILY_SALARY * 0.8: # Eric bid high yesterday
            bid = max(DAILY_SALARY * 0.9, eric_prev_bid + 5.0) # Try to outbid Eric with a margin
        elif highest_prev_bid > DAILY_SALARY * 0.6: # Other opponents bid moderately high
            bid = max(DAILY_SALARY * 0.7, highest_prev_bid + 2.0)
        else:
            bid = DAILY_SALARY * 0.8 # General competitive bid for tight supply
    elif current_supply > WATER_REQ * 2.5: # Abundant supply
        bid = DAILY_SALARY * 0.4 # Be more conservative
    else: # Medium supply scenario
        if eric_was_alive_yesterday and eric_prev_bid > DAILY_SALARY * 0.9: # Eric was very aggressive
            bid = max(DAILY_SALARY * 0.95, eric_prev_bid + 2.0)
        elif highest_prev_bid > DAILY_SALARY * 0.7: # Other opponents were quite aggressive
            bid = max(DAILY_SALARY * 0.8, highest_prev_bid + 1.0)
        # Else, use the default moderate bid (DAILY_SALARY * 0.6)

    # Ensure bid is at least a minimal amount to indicate intent for water
    bid = max(bid, DAILY_SALARY * 0.35) # Floor bid at 52.5

    # Ensure bid does not exceed available budget
    return min(my_status['budget'], bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # 1. If no opponents, bid minimum to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # 2. Collect yesterday's bids for alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # 3. Determine a base bid
    base_bid = DAILY_SALARY * 0.5 # Default moderate bid

    # 4. Adjust base bid based on previous bids (competitive reaction)
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest previous bid was very aggressive
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 3: # Not critically low HP, can be slightly less aggressive
                base_bid = max(DAILY_SALARY * 0.6, highest_prev_bid * 0.95)
            else: # Critical HP, must win, so bid very high
                base_bid = max(DAILY_SALARY * 0.9, highest_prev_bid * 1.05)
        else: # Moderate or low competition yesterday, try to win efficiently
            base_bid = max(DAILY_SALARY * 0.4, highest_prev_bid + 5)
    else: # No previous bids from alive opponents, or all were 0. Use a default competitive bid.
        base_bid = DAILY_SALARY * 0.55 # A bit more than default if no history

    # 5. Overriding adjustment for current HP (survival mode)
    if my_status['hp'] <= 2: # Very low HP, absolute priority to win water
        base_bid = min(my_status['budget'], DAILY_SALARY * 0.95)

    # 6. Adjust for current supply scarcity
    # Calculate total water requirement of all active participants (me + alive opponents)
    total_water_demand = WATER_REQ + sum(o['water_requirement'] for o in alive_opponents)
    
    # If supply is less than total demand, competition is higher.
    if day_context['supply'] < total_water_demand:
        shortage_ratio = total_water_demand / day_context['supply'] # Ratio > 1 means shortage
        # Increase bid more aggressively if shortage is severe, up to 50% increase
        base_bid *= min(1.5, 1 + (shortage_ratio - 1) * 0.5)
    else: # Supply is abundant (supply >= total_water_demand)
        # Decrease bid to save budget if supply is significantly more than demand
        excess_ratio = day_context['supply'] / total_water_demand # Ratio > 1 means excess
        if excess_ratio > 1.2: # If supply is at least 20% more than demand
            # Decrease bid, but not below 70% of current base_bid
            base_bid *= max(0.7, 1 - (excess_ratio - 1.2) * 0.3)

    # 7. Final bid validation: ensure it's within budget and at least a minimum value
    final_bid = max(1.0, min(my_status['budget'], base_bid))
    
    return final_bid
"""
