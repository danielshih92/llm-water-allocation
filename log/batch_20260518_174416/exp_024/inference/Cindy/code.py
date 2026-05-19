# ============================================================
# Experiment: exp_024
# Agent: Cindy
# Source: exp_024
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Default bid
    bid = DAILY_SALARY * 0.5

    # Analyze yesterday's bids from opponents
    max_prev_bid = 0
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            max_prev_bid = max(max_prev_bid, prev_trace['bid'])

    # Calculate total water needed by all alive players (including me)
    total_water_needed_by_all = WATER_REQ
    for opp in alive_opponents:
        total_water_needed_by_all += opp['water_requirement']

    current_supply = day_context['supply']

    # Strategy based on my HP and opponent's previous behavior
    if my_status['hp'] <= 2: # Critical HP: Bid very high
        bid = DAILY_SALARY * 0.95
        if max_prev_bid > 0:
            bid = max(bid, max_prev_bid + 1) # Try to outbid if there was a high bid yesterday
    elif my_status['hp'] <= 4: # Low HP: Bid high
        bid = DAILY_SALARY * 0.75
        if max_prev_bid > 0:
            bid = max(bid, max_prev_bid + 0.5) # Try to outbid
    else: # Healthy HP: Be strategic
        if num_alive_opponents == 0: # No opponents, bid minimum
            bid = WATER_REQ * 0.1 # Very low bid to save money
        elif current_supply >= total_water_needed_by_all: # Supply is abundant
            bid = DAILY_SALARY * 0.3 # Bid low to save money
            if max_prev_bid > 0:
                bid = min(bid, max_prev_bid * 0.9) # Bid slightly below if prev was high, but still low
        elif current_supply < WATER_REQ * (num_alive_opponents + 1) * 0.5: # Supply is very scarce
            # If healthy, let desperate opponents overpay, or bid just enough to be competitive
            if max_prev_bid > DAILY_SALARY * 0.8: # Opponents bidding very high
                bid = DAILY_SALARY * 0.4 # Consider saving money, let them fight
            else:
                bid = DAILY_SALARY * 0.6 # Moderate bid in scarcity
        else: # Normal competition
            if max_prev_bid > 0:
                bid = max(DAILY_SALARY * 0.5, max_prev_bid * 1.01) # Slightly above yesterday's max
            else:
                bid = DAILY_SALARY * 0.55 # Default competitive bid

    # Adjust bid for end-game
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] <= 4:
        # Last chance to survive, bid aggressively
        bid = max(bid, my_status['budget'] * 0.8)

    # Ensure bid is within budget and non-negative
    bid = min(bid, my_status['budget'])
    bid = max(0.0, bid)

    return round(bid, 2)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to save budget
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Base bid: A reasonable fraction of my daily salary
    bid = DAILY_SALARY * 0.6

    # Adjust based on my HP
    if my_hp <= 2: # Critical HP, must get water
        bid = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP, bid high
        bid = DAILY_SALARY * 0.8
    elif my_hp >= 8: # Healthy HP, can be more flexible
        # If supply is high, can be more conservative
        if current_supply > (MIN_SUPPLY + MAX_SUPPLY) / 2: # Above average supply
            bid = min(bid, DAILY_SALARY * 0.5)
        else:
            bid = max(bid, DAILY_SALARY * 0.6)

    # Adjust based on current supply
    # If supply is low, competition is higher, so bid more.
    # If supply is high, competition is lower, so bid less.
    supply_midpoint = (MIN_SUPPLY + MAX_SUPPLY) / 2.0
    if current_supply < supply_midpoint: # Below average supply
        bid += DAILY_SALARY * 0.1
    elif current_supply > supply_midpoint: # Above average supply
        bid -= DAILY_SALARY * 0.05

    # Adjust based on opponent's previous bids (yesterday's trace)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were bidding very high, I need to react.
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_hp <= 4: # Desperate
                bid = max(bid, highest_prev_bid + 5)
            else: # Healthy, but need to stay competitive
                bid = max(bid, highest_prev_bid * 0.95)

    # Final check: If it's the last few days and I'm healthy, I can afford to save.
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_hp > remaining_days: # Enough HP to survive remaining days without water
        bid = min(bid, DAILY_SALARY * 0.4)

    # Ensure bid doesn't exceed budget and is not negative
    bid = max(0.0, min(bid, my_budget))

    return bid
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
    
    alex_status = opponents_status.get('Alex')

    base_bid = DAILY_SALARY * 0.5 

    if my_status['hp'] <= 2: 
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: 
        base_bid = DAILY_SALARY * 0.8
    elif my_status['no_water_days'] > 0: 
        base_bid = DAILY_SALARY * 0.85
    
    num_players_can_be_satisfied = day_context['supply'] // WATER_REQ
    
    if num_players_can_be_satisfied < len(alive_opponents) + 1: 
        base_bid = max(base_bid, DAILY_SALARY * 0.6) 
        if day_context['supply'] < WATER_REQ * 1.5: 
             base_bid = max(base_bid, DAILY_SALARY * 0.75)

    alex_prev_bid = 0
    if alex_status and alex_status.get('previous_trace'):
        alex_prev_bid = alex_status['previous_trace'].get('bid', 0)
        
        if alex_prev_bid > DAILY_SALARY * 0.6:
            if my_status['hp'] <= 5:
                base_bid = max(base_bid, alex_prev_bid * 1.05) 
            else:
                base_bid = max(base_bid, alex_prev_bid * 0.9) 
        elif alex_prev_bid > 0 and alex_prev_bid < DAILY_SALARY * 0.4:
            base_bid = min(base_bid, max(DAILY_SALARY * 0.4, alex_prev_bid + 5))
            
    if day_context['day'] >= EPISODE_DAYS - 2: 
        if my_status['hp'] <= 5: 
            base_bid = DAILY_SALARY * 0.9
        else: 
            base_bid = max(base_bid, DAILY_SALARY * 0.6)
            
    final_bid = min(my_status['budget'], base_bid)
    
    if my_status['hp'] <= 1 and my_status['budget'] > 0:
        final_bid = my_status['budget']
    
    if final_bid < 10 and my_status['budget'] > 0 and my_status['hp'] > 2:
        final_bid = min(my_status['budget'], 15)

    return max(0.0, final_bid)
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

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # --- Step 1: Determine initial bid based on self-state and supply ---
    bid_amount = DAILY_SALARY * 0.5 # Default moderate bid

    # Adjust based on HP
    if my_status['hp'] <= 2: # Critical health
        bid_amount = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5: # Low health
        bid_amount = DAILY_SALARY * 0.8
    elif my_status['hp'] >= 10: # Healthy
        bid_amount = DAILY_SALARY * 0.45 # Can afford to be slightly less aggressive

    # Adjust based on supply scarcity (higher bid for lower supply)
    # Linear scaling: supply_factor is 1.2 at MIN_SUPPLY, 0.8 at MAX_SUPPLY
    # This means bid increases by 20% at min supply and decreases by 20% at max supply
    supply_factor = 1.2 - 0.4 * ((day_context['supply'] - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))
    bid_amount *= supply_factor

    # --- Step 2: Incorporate opponent's yesterday's bids ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents were very aggressive yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] <= 5: # Desperate, must win
                bid_amount = max(bid_amount, highest_prev_bid + 5)
            elif my_status['hp'] > 8: # Healthy, but competition is fierce, ensure we stay competitive
                bid_amount = max(bid_amount, average_prev_bid + 2)
            else: # Moderate HP
                bid_amount = max(bid_amount, highest_prev_bid + 1)
        # If opponents were relatively low yesterday
        elif highest_prev_bid < DAILY_SALARY * 0.5:
            if my_status['hp'] >= 10: # Healthy, conserve budget but still aim to win
                bid_amount = min(bid_amount, average_prev_bid + 1)
            else: # Need water, but don't overbid if not necessary
                bid_amount = max(bid_amount, average_prev_bid + 5)
        else: # Moderate opponent bids - try to outbid highest by a little
            bid_amount = max(bid_amount, highest_prev_bid + 1)

    # --- Step 3: Final adjustments and constraints ---
    final_bid = min(my_status['budget'], bid_amount)
    final_bid = max(1.0, final_bid) # Bid must be at least 1.0

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # Total days in the episode, from meta-round state

    supply = day_context['supply']
    day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        # No opponents, bid minimum to get water
        return max(1.0, min(my_budget, DAILY_SALARY * 0.1))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Calculate average and max bids from yesterday
    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Base bid strategy
    base_bid = DAILY_SALARY * 0.5

    # Adjust bid based on my HP and no_water_days
    if my_hp <= 2 or no_water_days > 0:
        # Critical survival mode: bid aggressively
        bid = DAILY_SALARY * 0.95
    elif my_hp <= 4:
        # Risky HP, be more competitive
        bid = DAILY_SALARY * 0.8
    else:
        # Healthy HP, start with a moderate bid
        bid = base_bid

    # Adjust based on supply and competition
    # Estimate total water units needed by all alive agents (including myself)
    total_water_units_demanded = WATER_REQ * (num_alive_opponents + 1)

    if supply < total_water_units_demanded * 0.75:
        # High scarcity: increase bid significantly
        bid = max(bid, max_yesterday_bid + 10.0, DAILY_SALARY * 0.8)
    elif supply > total_water_units_demanded * 1.25:
        # Abundant supply: try to save money
        bid = min(bid, DAILY_SALARY * 0.4, avg_yesterday_bid * 0.9 if avg_yesterday_bid > 0 else DAILY_SALARY * 0.4)
    else:
        # Moderate supply: react to yesterday's average
        bid = max(bid, avg_yesterday_bid + 2.0)

    # Late game aggression
    if day >= EPISODE_DAYS - 2: # Last 2 days
        bid = max(bid, DAILY_SALARY * 0.9)

    # Ensure bid does not exceed available budget
    bid = min(bid, my_budget)

    # Ensure bid is at least a minimal amount if I need water
    if bid <= 0 and (my_hp <= 5 or no_water_days > 0):
         bid = min(my_budget, DAILY_SALARY * 0.1) # Bid something if desperate and budget allows

    # Ensure bid is positive
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

    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # --- Determine my base bid based on my needs ---
    my_bid = DAILY_SALARY * 0.5 # Default conservative bid

    # If I'm desperate (low HP or missed water recently)
    if my_status['no_water_days'] > 0 or my_status['hp'] <= 2:
        my_bid = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 4 and current_day > EPISODE_DAYS / 3: # Mid-game low HP
        my_bid = DAILY_SALARY * 0.75
    elif my_status['hp'] <= 6 and current_day > EPISODE_DAYS / 2: # Late-game low HP
        my_bid = DAILY_SALARY * 0.8

    # --- Analyze opponents' previous day behavior from their trace ---
    yesterday_bids = []
    desperate_opponents_count = 0 # Opponents who didn't get water yesterday

    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])
            
            # Check if opponent didn't get water yesterday
            if prev_trace.get('status') == 'no_water':
                desperate_opponents_count += 1

    # --- Adjust my bid based on opponent analysis ---
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were generally aggressive yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            my_bid = max(my_bid, highest_prev_bid * 1.05) # Try to outbid
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            my_bid = max(my_bid, highest_prev_bid + 5) # Slightly outbid

    # If many opponents were desperate yesterday and supply is tight, we need to be aggressive
    # Supply is tight if it's less than enough for me AND one other player
    if desperate_opponents_count > 0 and current_supply < WATER_REQ * (num_alive_opponents + 0.5):
        if my_status['hp'] <= 4: # If I'm also low, I must fight hard
            my_bid = max(my_bid, DAILY_SALARY * 1.1)
        else: # Otherwise, increase bid to exploit their desperation or secure water
            my_bid = max(my_bid, DAILY_SALARY * 0.9)
    
    # If supply is very low (only enough for one player) and there are competitors
    if current_supply < WATER_REQ * 1.5 and num_alive_opponents > 0:
        if my_status['hp'] <= 3: # If I'm critically low, bid very high
            my_bid = max(my_bid, DAILY_SALARY * 1.2)
        elif my_status['no_water_days'] > 0:
             my_bid = max(my_bid, DAILY_SALARY * 1.1)
        else:
            # Otherwise, be a bit more aggressive to compete for scarce resource
            my_bid = max(my_bid, DAILY_SALARY * 0.7)

    # Final bid must not exceed budget
    final_bid = min(my_status['budget'], my_bid)

    # Ensure bid is at least 1 to participate
    final_bid = max(1.0, final_bid)

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

    # If no opponents are alive, bid minimally to secure water.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Calculate highest previous bid from active opponents
    highest_prev_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])

    # --- Bidding Strategy ---

    # Emergency condition: If HP is 1 or 2, I must win to survive.
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.99)

    # Late game pressure: Last 3 days (Day 8, 9, 10)
    if day_context['day'] >= EPISODE_DAYS - 2:
        if my_status['hp'] <= 4: # Low-ish health in late game
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        else: # Healthy enough for late game
            return min(my_status['budget'], DAILY_SALARY * 0.75)

    # Early to Mid-game (Day 1-7), not critically low HP
    # React to opponent's previous aggressive bidding
    if highest_prev_bid > DAILY_SALARY * 0.8: # Opponents are bidding high (above 120)
        if my_status['hp'] >= 8: # Very healthy, can afford to conserve or let others spend
            return min(my_status['budget'], DAILY_SALARY * 0.5)
        else: # HP is 3-7, need water soon, be aggressive
            return min(my_status['budget'], DAILY_SALARY * 0.85)
    else: # Opponents are not bidding super high (below or equal 120)
        if my_status['hp'] >= 8: # Very healthy, try to win cheaply or maintain pressure
            return min(my_status['budget'], max(DAILY_SALARY * 0.6, highest_prev_bid + 5.0))
        else: # HP is 3-7, need water soon, be more aggressive to win
            return min(my_status['budget'], max(DAILY_SALARY * 0.7, highest_prev_bid + 10.0))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQUIREMENT = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents_count = sum(1 for opp_data in opponents_status.values() if opp_data['alive'])

    if alive_opponents_count == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    strong_opponent_ids = ["Alex", "Eric"]
    
    competitive_opponents_data = []
    for agent_id, opp_status in opponents_status.items():
        if opp_status['alive'] and agent_id in strong_opponent_ids:
            competitive_opponents_data.append(opp_status)

    yesterday_bids = []
    for opp_data in competitive_opponents_data:
        prev = opp_data.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.6

    if my_hp <= 2:
        base_bid = DAILY_SALARY * 1.1
    elif my_hp <= 4:
        base_bid = DAILY_SALARY * 0.9
    elif my_hp >= 8:
        base_bid = DAILY_SALARY * 0.5

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 1.0:
            base_bid = max(base_bid, highest_prev_bid * 1.05)
        elif highest_prev_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, highest_prev_bid + (DAILY_SALARY * 0.1))

    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 1.05)
    elif remaining_days <= 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    num_possible_full_waters = int(current_supply // WATER_REQUIREMENT)
    if num_possible_full_waters == 1 and alive_opponents_count >= 1:
        base_bid = max(base_bid, DAILY_SALARY * 1.15)

    final_bid = min(my_budget, base_bid)

    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10
    MIN_SUPPLY = 15.0
    MAX_SUPPLY = 25.0

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents are alive, bid low to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid based on yesterday's highest pressure and my HP
    base_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Aggressive phase: if yesterday's highest bid was very high
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # Good HP, try to conserve or let others overspend
                base_bid = DAILY_SALARY * 0.4
            else: # Low HP, must secure water
                base_bid = DAILY_SALARY * 0.95
        # Moderate phase: if yesterday's highest bid was not extremely high
        else:
            # Bid slightly above highest previous bid, ensuring a minimum
            # Add a small buffer based on number of opponents to be more competitive
            base_bid = max(DAILY_SALARY * 0.55, highest_prev_bid + (DAILY_SALARY * 0.01 * num_alive_opponents))
    else: # No previous bids (e.g., Day 1 or all opponents are new)
        if my_status['hp'] <= 2: # Low HP, be aggressive
            base_bid = DAILY_SALARY * 0.9
        else: # Moderate HP, start with a reasonable bid
            base_bid = DAILY_SALARY * 0.55

    # --- Dynamic Adjustments ---

    # 1. Adjust for supply scarcity
    # If supply is low, increase bid. Scarcity is higher when supply is closer to MIN_SUPPLY.
    supply_level = day_context['supply']
    if supply_level <= WATER_REQ + num_alive_opponents: # Supply is tight relative to needs
        # Calculate a scarcity multiplier: 1.0 (max supply) to 1.3 (min supply)
        scarcity_multiplier = 1.0 + (MAX_SUPPLY - supply_level) / (MAX_SUPPLY - MIN_SUPPLY) * 0.3
        base_bid *= scarcity_multiplier

    # 2. Adjust for end-game pressure
    remaining_days = EPISODE_DAYS - day_context['day'] + 1
    if remaining_days <= 3: # Last 3 days, increase aggression
        if my_status['hp'] <= 2: # Critical HP, must win
            base_bid = max(base_bid, DAILY_SALARY * 0.98)
        else: # Moderate HP, still be aggressive to secure survival
            base_bid = max(base_bid, DAILY_SALARY * 0.8)
    elif my_status['hp'] <= 1: # Very critical HP, regardless of day, must win water
        base_bid = max(base_bid, DAILY_SALARY * 0.99)

    # Final bid must not exceed budget and be at least 1.0
    final_bid = max(1.0, min(my_status['budget'], base_bid))

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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o_id, o in opponents_status.items() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Calculate how many agents can get full water requirement
    max_winners_for_full_water = int(current_supply // WATER_REQ)

    # Base bid: Start with a percentage of daily salary, adjust based on competition
    base_bid = DAILY_SALARY * 0.65

    # 1. Adjust bid based on my HP and recent water status
    if my_hp <= 2: # Critical HP, bid very aggressively
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 5: # Low HP, bid aggressively
        base_bid = DAILY_SALARY * 0.85
    elif my_no_water_days > 0: # Missed water yesterday, need to secure today
        base_bid = DAILY_SALARY * 0.8
    
    # 2. Adjust bid based on competition intensity (number of opponents vs supply)
    if num_alive_opponents > 0:
        # If supply is very tight (e.g., only 1 full slot for 2+ players)
        if max_winners_for_full_water <= 1 and num_alive_opponents >= 1:
            base_bid = max(base_bid, DAILY_SALARY * 0.8)

        # Look at yesterday's winning bids from alive opponents to gauge market price
        yesterday_winning_bids = []
        for opp in alive_opponents:
            prev = opp.get('previous_trace', {})
            # Only consider bids that resulted in a win, as they reflect the market clearing price
            if prev and prev.get('bid') is not None and prev.get('status') == 'won':
                yesterday_winning_bids.append(prev['bid'])

        if yesterday_winning_bids:
            highest_prev_winning_bid = max(yesterday_winning_bids)
            # If the highest winning bid was high, we need to be competitive
            if highest_prev_winning_bid >= DAILY_SALARY * 0.7:
                base_bid = max(base_bid, highest_prev_winning_bid + 2.0)
            elif highest_prev_winning_bid >= DAILY_SALARY * 0.5:
                base_bid = max(base_bid, highest_prev_winning_bid + 1.0)
            else: # If yesterday's winning bids were low, ensure we bid above it but try to save
                base_bid = max(base_bid, highest_prev_winning_bid + 5.0)

    # 3. Adjust bid for late game aggression
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 3: # Last few days, prioritize survival
        if my_hp > 0:
            base_bid = max(base_bid, DAILY_SALARY * 0.9)
        else: # Already dead, no need to bid
            return 0.0

    # 4. Final bid calculation
    final_bid = min(my_budget, base_bid)

    # Ensure bid is not negative and has a reasonable floor if water is needed
    if my_hp <= 0: # If already dead, bid 0
        return 0.0
    
    # If budget is very low but I need water, bid what I have
    if my_budget > 0 and final_bid < DAILY_SALARY * 0.2 and (my_hp <= 5 or my_no_water_days > 0):
        final_bid = my_budget

    # Ensure a minimum bid if I have budget and need water
    if my_budget > 0 and final_bid < 1.0:
        final_bid = 1.0
    elif my_budget == 0: # If no budget, cannot bid
        final_bid = 0.0

    return round(float(final_bid), 2)
"""
