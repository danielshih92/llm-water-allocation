# ============================================================
# Experiment: exp_078
# Agent: Cindy
# Source: exp_078
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.15)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_bid = 0.0

    if my_status['hp'] <= 1:
        current_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 2:
        current_bid = DAILY_SALARY * 0.85
    elif my_status['hp'] <= 3:
        current_bid = DAILY_SALARY * 0.7
    else:
        current_bid = DAILY_SALARY * 0.5

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.75:
            if my_status['hp'] <= 2:
                current_bid = max(current_bid, highest_prev_bid + 5.0)
            else:
                current_bid = max(current_bid, highest_prev_bid * 1.05)
        else:
            current_bid = max(current_bid, highest_prev_bid + 1.0)

    current_supply = day_context['supply']
    if current_supply <= MIN_SUPPLY + (MAX_SUPPLY - MIN_SUPPLY) * 0.25:
        current_bid *= 1.1
    elif current_supply >= MAX_SUPPLY - (MAX_SUPPLY - MIN_SUPPLY) * 0.25:
        current_bid *= 0.9

    final_bid = min(my_status['budget'], max(0.0, current_bid))

    if final_bid < DAILY_SALARY * 0.05 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.05)

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
    num_alive_opponents = len(alive_opponents)

    # Base bid strategy - a moderate starting point
    base_bid = DAILY_SALARY * 0.5

    # Adjust bid based on my health and recent water acquisition
    if my_hp <= 2:  # Critical health
        base_bid = DAILY_SALARY * 0.95 # Bid very aggressively
    elif my_hp <= 4:  # Low health
        base_bid = DAILY_SALARY * 0.75 # Bid aggressively
    elif my_no_water_days > 0:  # Missed water yesterday
        base_bid = DAILY_SALARY * 0.8 # Prioritize getting water

    # Adjust bid based on opponents' previous bids from 'previous_trace'
    max_prev_bid = 0.0
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            max_prev_bid = max(max_prev_bid, prev_trace['bid'])

    if max_prev_bid > 0:
        if my_hp <= 4 or my_no_water_days > 0: # If I need water, try to outbid
            base_bid = max(base_bid, max_prev_bid + 5) # Bid slightly above the highest previous bid
        else: # If my HP is good, I can be more conservative but still competitive
            base_bid = max(base_bid, max_prev_bid * 0.9) # Match or slightly below, but ensure it's not too low

    # Further adjust based on number of active opponents
    if num_alive_opponents >= 3: # Higher competition
        base_bid *= 1.1
    elif num_alive_opponents == 1: # Less competition
        base_bid *= 0.9

    # Ensure a minimum aggressive bid if in dire need, even if opponents bid low
    if my_hp <= 2 or my_no_water_days > 0:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    # Ensure bid does not exceed available budget
    final_bid = min(my_budget, base_bid)

    # Ensure bid is non-negative
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    TOTAL_DAYS = 10 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and prev.get('bid') > 0:
            yesterday_bids.append(prev['bid'])

    competitive_yesterday_bids = [b for b in yesterday_bids if b >= DAILY_SALARY * 0.5]

    highest_prev_bid = 0
    if competitive_yesterday_bids:
        highest_prev_bid = max(competitive_yesterday_bids)

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    current_day = day_context['day']

    # Aggressive bidding if HP is critically low
    if my_current_hp <= 2:
        return min(my_current_budget, DAILY_SALARY * 1.1 + 10) 
    
    # High pressure if HP is low
    if my_current_hp <= 4:
        if highest_prev_bid > DAILY_SALARY * 0.8: 
            return min(my_current_budget, max(DAILY_SALARY * 0.95, highest_prev_bid + 5))
        else:
            return min(my_current_budget, DAILY_SALARY * 0.9)

    # Moderate HP, adjust based on previous bids
    if highest_prev_bid > DAILY_SALARY * 0.8: 
        # If it's late in the game and budget is good, be more aggressive
        if current_day >= TOTAL_DAYS - 2 and my_current_budget >= DAILY_SALARY * 2: 
            return min(my_current_budget, highest_prev_bid + 10)
        
        # Otherwise, try to win but with some budget conservation
        return min(my_current_budget, max(DAILY_SALARY * 0.75, highest_prev_bid + 2))
    
    elif highest_prev_bid > 0: 
        return min(my_current_budget, max(DAILY_SALARY * 0.6, highest_prev_bid + 1))
    
    else: 
        return min(my_current_budget, DAILY_SALARY * 0.65)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQUIREMENT = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta_round_state

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_budget = my_status['budget']
    my_hp = my_status['hp']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no active opponents, bid minimum to get water
    if not alive_opponents:
        return min(my_budget, 1.0)

    # Calculate a base bid
    base_bid = DAILY_SALARY * 0.5 # Default to half salary

    # Adjust bid based on my HP
    if my_hp <= 2: # Critical HP, bid almost everything
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP, bid high
        base_bid = DAILY_SALARY * 0.8
    elif my_hp >= 8 and current_day < EPISODE_DAYS * 0.7: # Healthy and early/mid game, can save a bit
        base_bid = DAILY_SALARY * 0.45

    # Adjust bid based on day progression
    # Increase bid as days progress to ensure survival towards the end
    # Linear increase: from 0 at day 1 to 0.3 * DAILY_SALARY at day 10
    day_pressure_bonus = (current_day / EPISODE_DAYS) * DAILY_SALARY * 0.3
    base_bid += day_pressure_bonus

    # Adjust bid based on supply availability
    # If supply is very tight (only enough for one or barely two)
    if current_supply <= WATER_REQUIREMENT + 2: # e.g., 15-16 water, very competitive
        base_bid *= 1.15 # Increase bid
    elif current_supply >= WATER_REQUIREMENT * 2 - 2: # e.g., 24-25 water, enough for two
        base_bid *= 0.85 # Decrease bid, less competition

    # React to opponent's previous bids (yesterday's trace)
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If someone bid high yesterday, assume pressure is on
        if max_yesterday_bid >= DAILY_SALARY * 0.7:
            # Bid slightly above their max, or ensure my base bid is at least this high
            base_bid = max(base_bid, max_yesterday_bid + 5)
        elif avg_yesterday_bid < DAILY_SALARY * 0.4: # If opponents bid low, try to save
            # Only if my HP is good, otherwise still prioritize survival
            if my_hp > 5:
                base_bid = min(base_bid, avg_yesterday_bid * 1.1 + 1)
            else: # If HP is low, don't risk it too much, bid a bit higher than avg
                base_bid = max(base_bid, avg_yesterday_bid + 10)

    # Final bid must be non-negative and within budget
    final_bid = max(0.0, min(my_budget, base_bid))

    # Critical survival override: If very low HP on last few days, bid almost everything
    if my_hp <= 1 and current_day >= EPISODE_DAYS - 2:
        final_bid = my_budget * 0.99

    # Another safety net for very low HP: ensure bid is at least a significant portion of salary
    if my_hp <= 2 and final_bid < DAILY_SALARY * 0.7:
        final_bid = min(my_budget, DAILY_SALARY * 0.75)

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
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    total_opponent_water_requirement = 0.0
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])
        total_opponent_water_requirement += opp['water_requirement']

    current_supply = day_context['supply']
    
    base_bid = DAILY_SALARY * 0.5 

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid > DAILY_SALARY * 0.3:
            base_bid = max(base_bid, highest_prev_bid + (DAILY_SALARY * 0.05))
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.4)

    bid = base_bid

    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        bid = max(bid, DAILY_SALARY * 0.95)
        if day_context['day'] >= EPISODE_DAYS - 2:
            bid = max(bid, DAILY_SALARY * 1.1)

    # If supply is less than total demand, competition will be high
    if float(current_supply) < (WATER_REQ + total_opponent_water_requirement):
        bid = max(bid, DAILY_SALARY * 0.8)

    bid = min(my_status['budget'], bid)
    
    bid = max(1.0, bid) 
    
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

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

    current_bid = DAILY_SALARY * 0.5

    # Adjust based on my HP
    if my_status['hp'] <= 2:
        current_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5:
        current_bid = DAILY_SALARY * 0.75
    elif my_status['hp'] >= 9:
        current_bid = DAILY_SALARY * 0.4

    # Adjust based on opponent's highest previous bid
    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] <= 3:
                current_bid = max(current_bid, highest_prev_bid + 5)
            else:
                current_bid = max(current_bid, highest_prev_bid * 0.9)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            current_bid = max(current_bid, highest_prev_bid + 2)
        else:
            current_bid = max(current_bid, highest_prev_bid * 1.1)

    # Adjust based on supply scarcity
    total_water_needed = WATER_REQ
    for opp in alive_opponents:
        total_water_needed += opp['water_requirement']

    if day_context['supply'] < total_water_needed / 2:
        current_bid *= 1.2
    elif day_context['supply'] < total_water_needed:
        current_bid *= 1.1
    elif day_context['supply'] >= total_water_needed * 1.5:
        current_bid *= 0.8
    elif day_context['supply'] >= total_water_needed:
        current_bid *= 0.9

    # Adjust based on day progression
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2:
        if my_status['hp'] <= 5:
            current_bid = max(current_bid, DAILY_SALARY * 0.95)
        else:
            current_bid = max(current_bid, DAILY_SALARY * 0.8)
    elif day_context['day'] <= 3:
        if my_status['hp'] > 5:
            current_bid = min(current_bid, DAILY_SALARY * 0.6)

    final_bid = max(1.0, current_bid)
    final_bid = min(final_bid, my_status['budget'])

    if my_status['hp'] <= 2:
        final_bid = min(final_bid, my_status['budget'])
    else:
        final_bid = min(final_bid, DAILY_SALARY * 1.2)

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to save budget.
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Initialize base bid
    bid_amount = DAILY_SALARY * 0.7 # A default moderate bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # React to highest previous bid based on game theory example:
        if highest_prev_bid >= DAILY_SALARY * 0.85: # Opponents were very aggressive (e.g., > 127.5)
            if my_hp > 3: # My HP is good, can afford to be conservative and save budget
                bid_amount = DAILY_SALARY * 0.3
            else: # My HP is low, must bid aggressively to survive
                bid_amount = DAILY_SALARY * 0.95
        else: # Opponents were less aggressive (e.g., < 127.5)
            # Bid to win but don't overpay, ensure it's at least a moderate amount
            bid_amount = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)
    else:
        # No previous bids from active opponents (e.g., Day 1 or all opponents are new/inactive)
        # Fallback to HP-based strategy
        if my_hp <= 2: # Critical HP
            bid_amount = DAILY_SALARY * 0.9
        elif my_hp <= 5: # Low HP
            bid_amount = DAILY_SALARY * 0.75
        else: # Good HP
            bid_amount = DAILY_SALARY * 0.6

    # --- Further adjustments based on current day context --- 

    # Consider total demand vs supply. If supply is very tight, increase bid.
    total_active_water_req = WATER_REQ + sum(o['water_requirement'] for o in alive_opponents)
    if current_supply < total_active_water_req:
        # Scale bid upwards if competition is high due to scarcity
        scarcity_factor = (total_active_water_req / current_supply)
        # If scarcity_factor is > 1 (demand > supply), increase bid. Max increase by 15%
        if scarcity_factor > 1:
            bid_amount *= (1 + (min(scarcity_factor, 2.0) - 1) * 0.15) # Cap factor to avoid extreme bids

    # If it's a late day and budget is very low, might need to go all-in
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days > 0:
        if my_budget < (DAILY_SALARY * 0.8 * remaining_days) and my_hp <= 3:
            bid_amount = DAILY_SALARY * 0.99
        # If budget is very healthy and HP is good, can be more conservative
        elif my_budget > (DAILY_SALARY * 1.5 * remaining_days) and my_hp >= 8:
            bid_amount = min(bid_amount, DAILY_SALARY * 0.6)

    # Ensure bid does not exceed current budget
    final_bid = min(my_budget, bid_amount)

    # Ensure bid is always positive and not ridiculously low if I need water
    if final_bid < DAILY_SALARY * 0.1 and my_hp < 10: # If bid is too low and not at full health
        final_bid = min(my_budget, DAILY_SALARY * 0.2) # At least 20% salary

    final_bid = max(1.0, final_bid) # Minimum bid of 1.0

    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQUIREMENT = 13
    MY_DAILY_SALARY = 150
    TOTAL_DAYS = 10

    # Start with a base competitive bid
    bid_amount = MY_DAILY_SALARY * 0.7

    # --- Priority 1: Critical survival --- 
    # These conditions set a high floor for the bid, overriding lower base bids.
    if my_status['hp'] <= 2:
        # Absolutely must get water. Bid very high, near full salary or more.
        bid_amount = MY_DAILY_SALARY * 1.1 # Aggressive bid to secure
    elif my_status['hp'] <= 4 or my_status['no_water_days'] > 0:
        # Low health or missed water, high priority to secure water.
        bid_amount = max(bid_amount, MY_DAILY_SALARY * 0.95)

    # --- Priority 2: End-game aggression --- 
    days_left = TOTAL_DAYS - day_context['day']
    if days_left <= 2:
        bid_amount = max(bid_amount, MY_DAILY_SALARY * 1.0) # Ensure high bid in final days
        # If I have a large budget, I can afford to outspend even more
        if my_status['budget'] / (days_left + 1) > MY_DAILY_SALARY * 1.5:
             bid_amount = max(bid_amount, MY_DAILY_SALARY * 1.2) # Very aggressive

    # --- Priority 3: Supply pressure adjustment ---
    # Low supply -> higher bid, High supply -> slightly lower bid
    supply_normalized = (day_context['supply'] - 15) / (25 - 15) # Normalize supply to 0-1 range
    supply_pressure_factor = (0.5 - supply_normalized) * 0.2 # Max +/- 10% of salary as a factor
    bid_amount *= (1 + supply_pressure_factor) # Multiplicative adjustment

    # --- Priority 4: Opponent reaction based on previous day's highest bid ---
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest previous bid is significantly higher than my current bid, I need to match/exceed.
        # This is especially important if my HP is not super high, or supply is tight.
        if highest_prev_bid > bid_amount * 1.05:
            bid_amount = max(bid_amount, highest_prev_bid * 1.02) # Bid slightly above to win
        # If my bid is much higher than opponents, I'm healthy, and supply is abundant, I can try to save.
        elif bid_amount > highest_prev_bid * 1.2 and my_status['hp'] > 5 and day_context['supply'] > MY_WATER_REQUIREMENT * 1.5:
            bid_amount = min(bid_amount, highest_prev_bid + 1) # Bid just above to save budget
        else: 
            # Otherwise, stay competitive around their highest bid to avoid being outbid
            bid_amount = max(bid_amount, highest_prev_bid * 0.98) # Ensure I'm not too low

    # --- Final check: Budget and minimum bid ---
    final_bid = min(my_status['budget'], bid_amount)

    # Ensure a reasonable minimum bid if budget allows, to prevent bidding 0 and losing HP unnecessarily
    if final_bid < MY_DAILY_SALARY * 0.1 and my_status['budget'] >= MY_DAILY_SALARY * 0.1:
        final_bid = MY_DAILY_SALARY * 0.1
    elif final_bid < 1.0 and my_status['budget'] >= 1.0:
        final_bid = 1.0
    elif final_bid < 0:
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
    EPISODE_DAYS = 10 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.05))

    # Base bid: a moderate amount of salary
    bid = DAILY_SALARY * 0.6 # 90.0

    # Adjust bid based on my urgency
    # If I have no water days, or low HP, I need water more desperately
    if my_status['no_water_days'] > 0:
        bid = DAILY_SALARY * 0.85 # 127.5
    elif my_status['hp'] <= WATER_REQ + 5: # If my HP is 18 or less
        bid = DAILY_SALARY * 0.75 # 112.5

    # If HP is critically low (will die without water next turn)
    if my_status['hp'] <= WATER_REQ:
        bid = DAILY_SALARY * 0.95 # 142.5

    # Analyze opponent's previous bids to inform current bid
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_opp_bid = max(yesterday_bids)
        # If my current calculated bid is not enough to beat the highest previous opponent bid,
        # try to outbid it by a small margin.
        if bid <= highest_prev_opp_bid:
            bid = highest_prev_opp_bid + 5 # Try to win by bidding slightly higher

    # Consider the day of the episode. Towards the end, competition might intensify.
    # day_context['day'] is 1-indexed.
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days
        if my_status['hp'] <= WATER_REQ + 10: # If HP is getting low towards the end
            bid = max(bid, DAILY_SALARY * 0.9) # Be very aggressive

    # Cap bid at a maximum percentage of salary (e.g., 99%) to avoid overspending unnecessarily
    # But allow higher if HP is critically low.
    if my_status['hp'] <= WATER_REQ:
        bid = min(bid, DAILY_SALARY * 0.99)
    else:
        bid = min(bid, DAILY_SALARY * 0.9) # General cap for non-critical situations

    # Ensure bid does not exceed budget and is not negative
    bid = min(my_status['budget'], bid)
    bid = max(0.0, bid) # Ensure bid is non-negative

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_competitors = len(alive_opponents)

    water_slots = int(day_context['supply'] // WATER_REQ)

    # If I'm the only one or competition is minimal, bid low to save budget
    if num_competitors == 0 or (num_competitors == 1 and water_slots >= 2):
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Default bid if no previous bids are available or for initial estimation
    base_bid = DAILY_SALARY * 0.5

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # High competition detected from yesterday's bids
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1:
                base_bid = DAILY_SALARY * 0.98
            elif num_competitors + 1 > water_slots:
                base_bid = max(DAILY_SALARY * 0.85, highest_prev_bid + 2)
            else:
                base_bid = max(DAILY_SALARY * 0.7, highest_prev_bid * 0.95)
        # Moderate competition
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1:
                base_bid = DAILY_SALARY * 0.9
            elif num_competitors + 1 > water_slots:
                base_bid = max(DAILY_SALARY * 0.7, average_prev_bid + 1)
            else:
                base_bid = max(DAILY_SALARY * 0.55, average_prev_bid + 1)
        # Low competition
        else:
            if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1:
                base_bid = DAILY_SALARY * 0.8
            else:
                base_bid = max(DAILY_SALARY * 0.3, highest_prev_bid + 1)
    else: # No previous bids (e.g., first day of episode)
        if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1:
            base_bid = DAILY_SALARY * 0.9
        else:
            base_bid = DAILY_SALARY * 0.55

    # Adjust bid based on my current health and "no water days"
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        base_bid = max(base_bid, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 5:
        base_bid = max(base_bid, DAILY_SALARY * 0.75)
    
    # Consider remaining days, be more aggressive towards the end if needed
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] < 10:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)

    final_bid = min(my_status['budget'], base_bid)
    final_bid = max(final_bid, 1.0)

    return final_bid
"""
