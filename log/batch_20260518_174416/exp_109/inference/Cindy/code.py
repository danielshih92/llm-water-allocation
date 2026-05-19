# ============================================================
# Experiment: exp_109
# Agent: Cindy
# Source: exp_109
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state, useful for end-game

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    current_supply = day_context['supply']
    current_day = day_context['day']

    # --- Strategy when alone ---
    if not alive_opponents:
        # If no opponents, bid just enough to secure water at minimum cost
        return min(my_status['budget'], 15) # Bid 15, which is 10% of salary, safe bet

    # --- General strategy with opponents ---

    # Get yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        # Only consider valid bids from alive opponents that didn't error or get eliminated
        if prev and prev.get('bid') is not None and prev.get('status') not in ['error', 'eliminated']:
            yesterday_bids.append(prev['bid'])

    # Determine base bid
    base_bid = DAILY_SALARY * 0.4 # Default medium bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents bid very high yesterday, they might be desperate or trying to win.
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Very high bid from opponent
            if my_status['hp'] <= 2: # Critical HP
                base_bid = max(highest_prev_bid + 5, DAILY_SALARY * 0.95) # Bid to win
            else: # Not critical, but competitive
                base_bid = max(highest_prev_bid + 1, DAILY_SALARY * 0.7) # Try to win, but not desperate
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Medium-high bid
            if my_status['hp'] <= 3:
                base_bid = max(highest_prev_bid + 2, DAILY_SALARY * 0.8)
            else:
                base_bid = max(highest_prev_bid + 1, DAILY_SALARY * 0.6)
        else: # Low bids from opponents yesterday, maybe save
            base_bid = max(DAILY_SALARY * 0.3, highest_prev_bid + 1) # Still competitive but save a bit

    # Adjust bid based on my HP
    if my_status['hp'] <= 1: # Extremely critical, must get water
        base_bid = DAILY_SALARY * 0.98 # Almost max bid
    elif my_status['hp'] <= 2: # Very critical
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif my_status['hp'] <= 3 and my_status['no_water_days'] > 0: # Low HP and missed water yesterday
        base_bid = max(base_bid, DAILY_SALARY * 0.85)

    # Adjust bid based on supply scarcity
    # How many agents can potentially get water if they all need WATER_REQ (my requirement)?
    num_slots_available = int(current_supply // WATER_REQ)

    if num_alive_opponents >= 1:
        # If not everyone can get water based on available slots
        if num_slots_available < (num_alive_opponents + 1): 
            base_bid = max(base_bid, DAILY_SALARY * 0.7)
        # If supply is very tight, only enough for one or two agents
        if num_slots_available <= 1: 
            base_bid = max(base_bid, DAILY_SALARY * 0.85)

    # End game strategy (last few days)
    if current_day >= (EPISODE_DAYS - 2): # Last 2 days
        if my_status['hp'] <= 3: # If I'm low on HP, bid aggressively to survive final days
            base_bid = max(base_bid, DAILY_SALARY * 0.99)
        elif my_status['budget'] >= DAILY_SALARY * 5: # If I have a lot of money, can afford to bid high to win
            base_bid = max(base_bid, DAILY_SALARY * 0.8)

    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure bid is at least a minimum positive value if budget allows
    if final_bid <= 0 and my_status['budget'] > 0:
        final_bid = 1 # A minimal bid if calculated bid is zero or negative

    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Base bid: a solid percentage of daily salary, reflecting general competition
    base_bid = DAILY_SALARY * 0.7

    # Adjust bid based on my current HP (prioritize survival)
    if my_status['hp'] <= 3: # Critical HP, need water desperately
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 6: # Low HP
        base_bid = DAILY_SALARY * 0.85
    elif my_status['hp'] > 8 and my_status['budget'] > DAILY_SALARY * 2: # Healthy and good budget, can be a bit less aggressive
        base_bid = DAILY_SALARY * 0.6

    # Adjust bid based on the day (become more aggressive towards the end if not healthy)
    if day_context['day'] >= EPISODE_DAYS - 3 and my_status['hp'] < 10:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)

    # Consider opponent's yesterday's bids to react to competition
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if my_status['hp'] <= 6: # If low HP, must win, bid aggressively above opponent
            base_bid = max(base_bid, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents are bidding very high, stay competitive
            base_bid = max(base_bid, highest_prev_bid + 2)
        else: # Opponents bidding moderately, try to win slightly above them
            base_bid = max(base_bid, highest_prev_bid + 1)
            
    # Adjust for tight supply: if supply is less than what all alive opponents need
    # This condition is almost always true for 2+ opponents, reinforcing aggressive bidding
    if num_alive_opponents > 0 and day_context['supply'] < WATER_REQ * num_alive_opponents:
        base_bid = base_bid * 1.05 # A small boost for tight supply

    # Final bid must not exceed current budget and be at least a minimum value
    final_bid = min(my_status['budget'], base_bid)
    return max(0.1, final_bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta_round_state

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid - a moderate amount, aiming for survival and some budget saving
    base_bid = DAILY_SALARY * 0.55

    # Aggressive bidding if HP is critical or missed water yesterday
    # If HP is less than 1.5 days of water or I've missed water previously
    if my_hp <= WATER_REQ * 1.5 or my_no_water_days > 0:
        base_bid = DAILY_SALARY * 0.85 # High bid to ensure survival

    # Analyze opponent's previous bids to adjust competitiveness
    yesterday_opp_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_opp_bids.append(prev['bid'])

    if yesterday_opp_bids:
        max_opp_bid_yesterday = max(yesterday_opp_bids)
        # If the highest opponent bid yesterday was significant, react
        if max_opp_bid_yesterday > DAILY_SALARY * 0.4: # If their max bid was serious
            # If supply is tight (not enough for everyone to get their water_req),
            # bid higher than them to secure water.
            if current_supply < WATER_REQ * (num_alive_opponents + 1):
                base_bid = max(base_bid, max_opp_bid_yesterday + 5) # Try to outbid them by a small margin
            else:
                # If supply is not tight, we can be competitive without overbidding too much
                base_bid = max(base_bid, max_opp_bid_yesterday * 0.95) # Match closely

    # Adjust bid based on supply availability
    # If supply is very low (e.g., only enough for me or slightly more), increase bid
    if current_supply <= WATER_REQ * 1.5:
        base_bid = max(base_bid, DAILY_SALARY * 0.7)
    # If supply is abundant (enough for everyone), try to save budget
    elif current_supply >= WATER_REQ * (num_alive_opponents + 1):
        base_bid = min(base_bid, DAILY_SALARY * 0.5) # Try to get it cheaper

    # Progressive bidding as the game progresses
    # Bids tend to increase towards the end of the episode as budget becomes less critical than survival
    if current_day > EPISODE_DAYS * 0.7: # Last 30% of days
        base_bid = max(base_bid, DAILY_SALARY * 0.75) # Be more aggressive

    # Final bid must not exceed budget and must be at least a minimal amount
    final_bid = min(my_budget, base_bid)
    final_bid = max(final_bid, DAILY_SALARY * 0.1) # Ensure a minimum bid to participate

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
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    num_slots = int(current_supply / WATER_REQ)

    if num_slots == 0:
        if my_hp <= 2:
            return min(my_budget, DAILY_SALARY * 0.95)
        return min(my_budget, DAILY_SALARY * 0.1)

    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    current_bid = DAILY_SALARY * 0.6

    if my_hp <= 2:
        current_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4:
        current_bid = max(current_bid, DAILY_SALARY * 0.8)
    elif my_no_water_days > 0:
        current_bid = max(current_bid, DAILY_SALARY * 0.75)

    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2:
        current_bid = max(current_bid, DAILY_SALARY * 0.9)
    elif remaining_days <= 4:
        current_bid = max(current_bid, DAILY_SALARY * 0.7)

    highest_prev_bid = 0.0
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev_trace['bid'])

    if highest_prev_bid > 0:
        if my_hp <= 4 or my_no_water_days > 0:
            current_bid = max(current_bid, highest_prev_bid + 5.0)
        else:
            current_bid = max(current_bid, highest_prev_bid + 1.0)

    final_bid = min(my_budget, current_bid)

    if (my_hp <= 4 or my_no_water_days > 0) and final_bid < DAILY_SALARY * 0.4:
        final_bid = min(my_budget, DAILY_SALARY * 0.4)

    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_agents = len(alive_opponents) + 1 # Include myself

    # --- Step 1: Determine base bid based on my health ----
    # Prioritize survival if HP is critical
    if my_hp <= 2:
        base_bid = DAILY_SALARY * 0.95 # Very aggressive
    elif my_hp <= 4:
        base_bid = DAILY_SALARY * 0.80 # Aggressive
    else:
        base_bid = DAILY_SALARY * 0.60 # Moderate

    # --- Step 2: Analyze opponent bids from yesterday's trace ----
    yesterday_bids = []
    total_opponent_water_req = 0
    for opp in alive_opponents:
        total_opponent_water_req += opp['water_requirement']
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # --- Step 3: Assess competition based on supply and demand ----
    total_water_demand = WATER_REQ + total_opponent_water_req
    
    # Calculate how many agents could potentially get their water requirement satisfied
    # Using my WATER_REQ as a common unit for 'slots'
    num_water_slots = int(current_supply / WATER_REQ) # Critical: int()

    # Determine if competition is high or low
    is_high_competition = (current_supply < total_water_demand) or (num_water_slots < num_alive_agents)

    # --- Step 4: Adjust bid based on competition and opponent history ----
    bid_value = base_bid # Start with the health-adjusted base bid

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        if is_high_competition:
            # In high competition, aim to outbid strong opponents or at least the average
            # If my HP is very low, make sure to bid even higher
            if my_hp <= 2:
                bid_value = max(bid_value, max_prev_bid + 5.0, DAILY_SALARY * 0.98) # Almost max salary
            elif my_hp <= 4:
                bid_value = max(bid_value, max_prev_bid + 2.0, avg_prev_bid + 10.0)
            else:
                bid_value = max(bid_value, avg_prev_bid + 5.0) # Try to win against average
        else:
            # In low competition, try to conserve budget but still secure water
            bid_value = max(bid_value * 0.8, avg_prev_bid + 1.0, DAILY_SALARY * 0.25) # Lower but safe
            # Ensure it's not too low if HP is still a concern
            if my_hp <= 4:
                 bid_value = max(bid_value, DAILY_SALARY * 0.5)

    else: # No previous bids from opponents (e.g., Day 1 of the meta-round or no alive opponents)
        if is_high_competition:
            # Default aggressive bid if competition is expected
            if my_hp <= 2:
                bid_value = DAILY_SALARY * 0.9
            else:
                bid_value = DAILY_SALARY * 0.75
        else:
            # Default conservative bid
            bid_value = DAILY_SALARY * 0.4

    # --- Step 5: Final bid constraints ----
    final_bid = min(my_budget, bid_value)
    final_bid = max(1.0, final_bid) # Bid must be at least 1

    return final_bid
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

    # If no opponents, bid minimum to save budget
    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    # Base bid strategy
    # Default bid is a moderate percentage of daily salary
    bid = DAILY_SALARY * 0.6

    # Adjust bid based on my health and water status
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        # Critical state: Bid very high to ensure water
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        # Low health: Bid high
        bid = DAILY_SALARY * 0.85
    elif my_status['hp'] >= 8:
        # Healthy: Can afford to be slightly less aggressive, but still competitive
        bid = DAILY_SALARY * 0.55

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                yesterday_bids.append(prev_trace['bid'])

    # Adjust bid based on opponent's previous bidding behavior
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If the highest previous bid was significant, we need to be competitive
        # Add a small increment to beat it, but not too much if we are healthy
        if highest_prev_bid >= DAILY_SALARY * 0.7:
            if my_status['hp'] <= 4 or my_status['no_water_days'] > 0:
                # If desperate, ensure we bid above the highest previous bid
                bid = max(bid, highest_prev_bid + 5.0)
            else:
                # If healthy, still be competitive but not overly aggressive
                bid = max(bid, highest_prev_bid + 1.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.4:
            # If previous bids were moderate, ensure we are slightly above them
            bid = max(bid, highest_prev_bid + 2.0)

    # Consider supply vs. demand for general aggressiveness
    num_potential_winners = int(day_context['supply'] // WATER_REQ)
    num_bidders = len(alive_opponents) + 1 # Including myself

    if num_potential_winners < num_bidders:
        # Supply is less than demand, competition is high
        # If my bid is not already high due to desperation, increase it
        if bid < DAILY_SALARY * 0.7:
            bid = min(DAILY_SALARY * 0.8, bid * 1.1) # Increase by 10% up to 80% salary
    else:
        # Supply might be sufficient for everyone, can be less aggressive
        if bid > DAILY_SALARY * 0.5:
            bid = DAILY_SALARY * 0.5 # Reduce bid if it's too high and supply is good

    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], bid)

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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_players = len(alive_opponents) + 1 # Including myself

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    remaining_days = EPISODE_DAYS - day_context['day']

    bid_value = float(DAILY_SALARY)

    # 1. Supply Scarcity Adjustment
    total_demand = num_alive_players * WATER_REQ
    current_supply = day_context['supply']

    if current_supply < total_demand:
        scarcity_factor = total_demand / current_supply
        bid_value *= (1 + (scarcity_factor - 1) * 0.2)
    else:
        ample_factor = current_supply / total_demand
        bid_value *= (1 - (ample_factor - 1) * 0.1)

    bid_value = max(bid_value, DAILY_SALARY * 0.6)

    # 2. My HP Adjustment
    if my_status['hp'] <= 3:
        bid_value *= 1.25
    elif my_status['hp'] <= 6:
        bid_value *= 1.1

    # 3. Budget Management Adjustment
    if remaining_days > 0:
        my_avg_daily_budget = my_status['budget'] / remaining_days
        if my_avg_daily_budget < DAILY_SALARY * 0.75:
            bid_value *= 0.8
        elif my_avg_daily_budget > DAILY_SALARY * 1.5:
            bid_value *= 1.1

    # 4. Opponent Reaction (based on yesterday's bids)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid > DAILY_SALARY * 1.0:
            bid_value = max(bid_value, highest_prev_bid * 1.05)
        elif highest_prev_bid < DAILY_SALARY * 0.8:
            bid_value = max(bid_value, highest_prev_bid * 1.1)

    # 5. Last day desperation
    if day_context['day'] == EPISODE_DAYS - 1 and my_status['hp'] < 10:
        bid_value = my_status['budget'] * 0.95

    final_bid = max(1.0, min(my_status['budget'], bid_value))

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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    
    # Base bid: The value of 13 water is at least DAILY_SALARY
    # Adjust based on my HP
    if my_hp <= 2: # Critical condition, must get water
        bid = DAILY_SALARY * 1.15 # Aggressive to survive
    elif my_hp <= 4: # Low HP, strong need for water
        bid = DAILY_SALARY * 1.05 # Slightly aggressive
    else: # Healthy HP, can be more strategic or conservative
        bid = DAILY_SALARY * 0.9 # Conservative

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # Competition is always high for full water (supply 15-25, req 13) since only 1 agent can get full water.
        
        if my_hp <= 3: # If my HP is low, I need to be very competitive
            # Bid to beat the highest previous bid, with a margin
            bid = max(bid, highest_prev_bid + 5) 
            # If highest_prev_bid was very low, still ensure a decent bid
            bid = max(bid, DAILY_SALARY * 1.0) # Ensure at least salary value
        else: # If my HP is healthy, try to win but don't overspend too much
            # Bid slightly above average, but cap it to avoid overspending if others bid low
            bid = max(bid, average_prev_bid + 2)
            bid = min(bid, DAILY_SALARY * 1.1) # Cap healthy bids to 1.1x salary

    # End game strategy (last 2 days)
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2:
        if my_hp <= 3: # Must survive
            bid = max(bid, DAILY_SALARY * 1.25) # Very aggressive
        else: # Try to win, but conserve budget for final standing
            bid = min(bid, DAILY_SALARY * 0.95) # Slightly less aggressive than base

    # Final adjustments
    bid = min(bid, my_budget) # Never bid more than budget
    
    # Hard cap on bid to prevent irrational overspending, unless budget is very low and HP critical
    if my_hp <= 2:
        bid = min(bid, DAILY_SALARY * 1.5) # Max 1.5x salary if critical
    else:
        bid = min(bid, DAILY_SALARY * 1.2) # Max 1.2x salary otherwise

    bid = max(0.01, bid) # Bid must be positive

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

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and prev.get('day') == day_context['day'] - 1:
            yesterday_bids.append(prev['bid'])

    bid_value = DAILY_SALARY * 0.75

    if my_status['hp'] <= 2:
        bid_value = DAILY_SALARY * 0.98
    elif my_status['hp'] <= 4:
        bid_value = max(bid_value, DAILY_SALARY * 0.9)
    elif my_status['hp'] <= 6:
        bid_value = max(bid_value, DAILY_SALARY * 0.8)

    if day_context['day'] >= int(EPISODE_DAYS * 0.7):
        if my_status['hp'] <= 5:
            bid_value = max(bid_value, DAILY_SALARY * 0.95)
        else:
            bid_value = max(bid_value, DAILY_SALARY * 0.8)

    supply = day_context['supply']
    if supply < WATER_REQ:
        if my_status['hp'] <= 3:
            bid_value = max(bid_value, DAILY_SALARY * 0.99)
        else:
            bid_value = min(bid_value, DAILY_SALARY * 0.5)
    elif supply < WATER_REQ * 2:
        if my_status['hp'] <= 4:
            bid_value = max(bid_value, DAILY_SALARY * 0.92)
        else:
            bid_value = max(bid_value, DAILY_SALARY * 0.78)
    elif my_status['hp'] > 7:
        bid_value = min(bid_value, DAILY_SALARY * 0.65)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] <= 3:
                bid_value = max(bid_value, highest_prev_bid + 5)
            else:
                bid_value = max(bid_value, highest_prev_bid + 1)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            bid_value = max(bid_value, highest_prev_bid + 2)
        else:
            bid_value = max(bid_value, DAILY_SALARY * 0.65)

    final_bid = min(my_status['budget'], bid_value)
    final_bid = max(final_bid, DAILY_SALARY * 0.25)

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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid conservatively to save budget
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Get yesterday's bids from alive opponents to gauge competition
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid based on urgency
    base_bid = DAILY_SALARY * 0.6 # Default moderate bid

    if my_hp <= 2 or my_no_water_days >= 2: # Critical state: must get water
        base_bid = DAILY_SALARY * 0.95 # Bid very high
    elif my_hp <= 5 or my_no_water_days >= 1: # High urgency: need water soon
        base_bid = DAILY_SALARY * 0.85 # Bid high
    # Else: my_hp > 5 and my_no_water_days == 0, stable state, use base_bid = DAILY_SALARY * 0.6

    # Adjust bid based on opponent's previous behavior
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were very aggressive yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_hp <= 5 or my_no_water_days >= 1: # If I'm in need, try to outbid
                base_bid = max(base_bid, highest_prev_bid + 5) 
            else: # If stable but competition is high, still be competitive
                base_bid = max(base_bid, highest_prev_bid + 1)
        # If opponents were moderately aggressive
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            base_bid = max(base_bid, highest_prev_bid + 1)

    # Special logic for the final day(s) of the episode
    days_remaining = EPISODE_DAYS - current_day
    if days_remaining <= 1 and (my_hp <= 10 or my_no_water_days >= 1): 
        # If it's the last day or second to last, and I'm not full HP or missed water
        if my_hp <= 2 or my_no_water_days >= 1: # Critical, bid all for survival
            base_bid = my_budget 
        else: # Not critical but want to secure water on final days
            base_bid = max(base_bid, DAILY_SALARY * 0.9)

    # Ensure bid does not exceed available budget
    final_bid = min(my_budget, base_bid)

    # Ensure bid is non-negative. If budget is 0, bid 0.
    return max(0.0, final_bid)
"""
