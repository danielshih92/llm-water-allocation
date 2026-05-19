# ============================================================
# Experiment: exp_007
# Agent: Cindy
# Source: exp_007
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

    # If no opponents, bid conservatively but ensure water
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Calculate total water demand from all agents
    total_water_demand = WATER_REQ + sum(o['water_requirement'] for o in alive_opponents)
    supply = day_context['supply']

    # Bidding strategy when no previous bids are available (e.g., Day 1 or opponents didn't bid)
    if not yesterday_bids:
        if my_status['hp'] <= 2:  # Emergency: must secure water
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        
        # If supply is tight relative to total demand, bid moderately high
        if supply < total_water_demand * 1.2: 
            return min(my_status['budget'], DAILY_SALARY * 0.7)
        
        # Otherwise, bid moderately
        return min(my_status['budget'], DAILY_SALARY * 0.55)

    # Bidding strategy when previous bids are available
    highest_prev_bid = max(yesterday_bids)

    # Aggressive bidding if supply is very low relative to demand and HP is critical
    if supply < total_water_demand * 1.1: # Supply is tight
        if my_status['hp'] <= 3: # Must get water
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        else: # Can afford to be slightly less aggressive but still competitive
            return min(my_status['budget'], max(DAILY_SALARY * 0.7, highest_prev_bid + 5))
            
    # If highest previous bid was very high, react accordingly
    if highest_prev_bid >= DAILY_SALARY * 0.85: # Opponents bid very high
        if my_status['hp'] > 3: # My HP is good, try to save budget if possible
            return min(my_status['budget'], DAILY_SALARY * 0.4)
        else: # My HP is low, must secure water
            return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    # If supply is abundant, try to bid slightly lower than highest previous bid
    if supply > total_water_demand * 1.5: 
        return min(my_status['budget'], max(DAILY_SALARY * 0.4, highest_prev_bid * 0.9))
    
    # Default strategy: bid slightly above highest previous bid in normal competition
    return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    base_bid = DAILY_SALARY * 0.55

    # If supply is low relative to players, increase base bid
    if current_supply < WATER_REQ * (num_alive_opponents + 1): 
        base_bid = DAILY_SALARY * 0.65
    if current_supply < WATER_REQ * 2: 
        base_bid = DAILY_SALARY * 0.75

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    bid = base_bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.85: 
            if my_current_hp > 3: 
                bid = max(base_bid, highest_prev_bid * 0.98)
            else: 
                bid = max(base_bid, highest_prev_bid + 5)
                bid = max(bid, DAILY_SALARY * 0.95)
        elif highest_prev_bid >= DAILY_SALARY * 0.5: 
            bid = max(base_bid, highest_prev_bid + 2)
        else: 
            bid = max(base_bid, highest_prev_bid * 1.1)

    if my_current_hp <= 2: 
        bid = max(bid, DAILY_SALARY * 0.99)
    elif my_current_hp <= 4 and my_status['no_water_days'] > 0: 
        bid = max(bid, DAILY_SALARY * 0.90)

    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: 
        if my_current_hp <= 3: 
            bid = max(bid, DAILY_SALARY * 0.99)
        elif my_current_hp >= 8 and my_current_budget > DAILY_SALARY * 2: 
            bid = min(bid, DAILY_SALARY * 0.7)
            bid = max(bid, DAILY_SALARY * 0.4)

    final_bid = min(my_current_budget, bid)
    final_bid = max(1.0, final_bid)

    return float(final_bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid = DAILY_SALARY * 0.6 # Default bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 5:
                bid = DAILY_SALARY * 0.5
            else:
                bid = DAILY_SALARY * 0.95
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            if my_status['hp'] > 3:
                bid = max(DAILY_SALARY * 0.65, highest_prev_bid + 2.0)
            else:
                bid = DAILY_SALARY * 0.85
        else:
            if my_status['hp'] > 7:
                bid = DAILY_SALARY * 0.4
            elif my_status['hp'] > 3:
                bid = DAILY_SALARY * 0.55
            else:
                bid = DAILY_SALARY * 0.75
    else:
        if my_status['hp'] <= 3:
            bid = DAILY_SALARY * 0.9
        elif my_status['hp'] <= 7:
            bid = DAILY_SALARY * 0.7
        else:
            bid = DAILY_SALARY * 0.5

    if current_supply <= 17.0:
        bid *= 1.1
    elif current_supply >= 23.0:
        bid *= 0.9

    bid = max(1.0, bid)
    bid = min(bid, my_status['budget'])

    return bid
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    supply = day_context['supply']
    
    normalized_supply = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    salary_multiplier = 0.8 - (normalized_supply * 0.4) 
    base_bid = DAILY_SALARY * salary_multiplier

    previous_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            previous_bids.append(prev['bid'])

    max_prev_bid = 0
    if previous_bids:
        max_prev_bid = max(previous_bids)
    
    current_bid = max(base_bid, max_prev_bid + 1.0)
    
    is_desperate = False
    if my_status['hp'] <= 3:
        is_desperate = True
    if my_status['no_water_days'] >= 1:
        is_desperate = True
    if day_context['day'] >= EPISODE_DAYS - 2 and my_status['hp'] > 0:
        is_desperate = True

    if is_desperate:
        current_bid = max(current_bid, DAILY_SALARY * 0.95)
        if my_status['budget'] > DAILY_SALARY * 1.2:
             current_bid = max(current_bid, DAILY_SALARY * 1.1)

    final_bid = min(my_status['budget'], current_bid)
    
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    my_water_requirement = 13
    daily_salary = 150
    episode_days = 10
    min_supply = 15
    max_supply = 25

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid calculation
    base_bid = daily_salary * 0.5 # A moderate starting point

    # Adjust bid based on HP
    if my_hp <= 2: # Critical HP
        base_bid = daily_salary * 0.95
    elif my_hp <= 5: # Low HP
        base_bid = daily_salary * 0.8
    elif my_hp >= 8: # Healthy HP, can be a bit more conservative
        base_bid = daily_salary * 0.4

    # Adjust bid based on supply
    supply_factor = 1.0
    if current_supply <= min_supply + 2: # Very low supply
        supply_factor = 1.2
    elif current_supply >= max_supply - 2: # Very high supply
        supply_factor = 0.8
    else: # Medium supply, scale factor based on how far from avg supply
        avg_supply = (min_supply + max_supply) / 2
        supply_factor = 1.0 + (avg_supply - current_supply) / (max_supply - min_supply) * 0.2

    base_bid *= supply_factor

    # Adjust bid based on opponent's previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents are bidding very high, try to outbid if necessary
        if highest_prev_bid > daily_salary * 0.8:
            base_bid = max(base_bid, highest_prev_bid * 1.05)
        # If opponents are bidding very low, don't overbid too much
        elif highest_prev_bid < daily_salary * 0.3:
            base_bid = min(base_bid, highest_prev_bid * 1.2)

    # Consider end-game strategy
    remaining_days = episode_days - current_day
    if remaining_days <= 3: # Last few days
        if my_hp < 5: # Critical HP in end game
            base_bid = max(base_bid, daily_salary * 0.9)
        elif my_budget > daily_salary * remaining_days * 1.5: # If I have a lot of budget, I can push
             base_bid = max(base_bid, daily_salary * 0.7)

    # Ensure bid is within budget
    final_bid = min(my_budget, base_bid)

    # Ensure bid is at least a minimum to be competitive, but not 0 if alive
    if final_bid < daily_salary * 0.1 and my_hp > 0:
        final_bid = max(final_bid, daily_salary * 0.1)

    # If I'm dead or near death and no budget, bid 0
    if my_hp <= 0 or my_budget <= 0:
        return 0.0

    return round(max(0.0, final_bid), 2)
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
    remaining_days = EPISODE_DAYS - current_day + 1
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid low to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Calculate estimated water competition
    total_water_needed_by_others = sum(o['water_requirement'] for o in alive_opponents)
    total_demand_including_me = WATER_REQ + total_water_needed_by_others
    
    # Initial base bid: A fraction of daily salary
    base_bid = DAILY_SALARY * 0.6
    
    # Adjust bid based on remaining budget and days
    if my_status['budget'] < DAILY_SALARY * remaining_days and remaining_days > 1:
        base_bid = DAILY_SALARY * 0.5
        if my_status['hp'] <= 3:
            base_bid = DAILY_SALARY * 0.75
    
    # React to yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Adjust bid based on yesterday's highest bid and my HP
    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.8: # If opponents bid very high
            if my_status['hp'] <= 3 or my_status['no_water_days'] > 0:
                base_bid = max(base_bid, highest_prev_bid + 5)
                base_bid = max(base_bid, DAILY_SALARY * 0.95)
            else:
                base_bid = max(base_bid, highest_prev_bid * 1.05)
                base_bid = min(base_bid, DAILY_SALARY * 1.2)
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderate bids
            base_bid = max(base_bid, highest_prev_bid + 1)
            base_bid = min(base_bid, DAILY_SALARY * 0.8)
        else: # Low bids from opponents
            base_bid = max(base_bid, highest_prev_bid + 0.5)
            base_bid = min(base_bid, DAILY_SALARY * 0.6)
    
    # Strong adjustment for low HP or consecutive no-water days
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)

    # If supply is very tight relative to total demand, bid higher
    if total_demand_including_me > 0 and day_context['supply'] < total_demand_including_me:
        supply_per_req = day_context['supply'] / total_demand_including_me
        if supply_per_req < 1.0:
            base_bid = max(base_bid, DAILY_SALARY * (1.0 + (1.0 - supply_per_req) * 0.5))
            base_bid = min(base_bid, DAILY_SALARY * 1.5)

    # Final bid must not exceed current budget
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

    # Identify Alex and his previous bid
    alex_status = opponents_status.get('Alex')
    alex_yesterday_bid = 0
    if alex_status and alex_status['alive']:
        alex_prev_trace = alex_status.get('previous_trace')
        if alex_prev_trace and alex_prev_trace.get('bid') is not None:
            alex_yesterday_bid = alex_prev_trace['bid']

    # Calculate how many full water requirements can be met by current supply
    potential_winners = int(day_context['supply'] // WATER_REQ)

    # Base bid, usually a portion of daily salary
    base_bid = DAILY_SALARY * 0.8

    # --- Bidding Logic ---

    # 1. Critical HP: If HP is very low, bid aggressively to survive
    if my_status['hp'] <= 2:
        # Bid very high, slightly above Alex's potential high bid, capped by budget
        # Add a buffer to ensure winning
        return min(my_status['budget'], max(DAILY_SALARY * 1.2, alex_yesterday_bid + 10))

    # 2. High competition due to scarce supply (1 or 0 potential winners)
    if potential_winners <= 1:
        if alex_yesterday_bid > DAILY_SALARY * 0.7: # Alex is a strong bidder
            # Bid slightly higher than Alex's previous bid to secure water
            bid = max(base_bid, alex_yesterday_bid + 5)
            return min(my_status['budget'], bid)
        else:
            # Alex is not bidding high, but supply is still scarce. Bid firmly.
            return min(my_status['budget'], DAILY_SALARY * 1.0)
    
    # 3. Moderate competition / Abundant supply (2 or more potential winners)
    else:
        if alex_yesterday_bid > DAILY_SALARY * 0.8 and my_status['hp'] <= 4:
            # Alex is still strong, and my HP is not perfectly healthy. Be competitive.
            return min(my_status['budget'], max(base_bid, alex_yesterday_bid + 2))
        elif my_status['hp'] <= 4:
            # My HP is a bit low, but supply is good. Bid reasonably to stay healthy.
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        else:
            # Healthy HP, abundant supply. Can bid more conservatively.
            return min(my_status['budget'], DAILY_SALARY * 0.75)

    # Fallback (should ideally not be reached)
    return min(my_status['budget'], base_bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    # Calculate my maximum affordable bid per unit
    max_affordable_bid_per_unit = my_status['budget'] / WATER_REQ if WATER_REQ > 0 else 0
    
    # Calculate a fair price per unit based on my daily salary
    fair_price_per_unit = DAILY_SALARY / WATER_REQ if WATER_REQ > 0 else 0

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # --- Phase 1: Emergency & End Game Bidding --- 
    # If HP is very low, bid aggressively to survive
    if my_status['hp'] <= 2:
        # Bid significantly above fair price, up to a high premium
        return min(max_affordable_bid_per_unit, fair_price_per_unit * 1.5)
    
    # If it's the last few days, bid higher to secure survival
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] <= 5: # If low HP in end game
        return min(max_affordable_bid_per_unit, fair_price_per_unit * 1.3)
    elif remaining_days <= 2: # End game, but HP is okay
        return min(max_affordable_bid_per_unit, fair_price_per_unit * 1.1)

    # --- Phase 2: Opponent-aware Bidding --- 
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Calculate total water demand vs supply
    total_water_demand = WATER_REQ # My requirement
    for opp in alive_opponents:
        total_water_demand += opp['water_requirement']
    
    supply = day_context['supply']

    # Determine base bid for this turn
    current_bid = fair_price_per_unit * 0.8 # Start with a conservative bid

    if not alive_opponents:
        # If no opponents, bid very low but ensure I get water
        current_bid = fair_price_per_unit * 0.3
    elif yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If demand exceeds supply, competition is high
        if total_water_demand > supply:
            # Bid slightly above the highest previous bid, with a minimum floor
            current_bid = max(current_bid, highest_prev_bid + (fair_price_per_unit * 0.05)) # Add 5% of fair price
            # If highest bid was already very high, be prepared to bid more aggressively
            if highest_prev_bid >= fair_price_per_unit * 1.0:
                 current_bid = max(current_bid, highest_prev_bid + (fair_price_per_unit * 0.1)) # Add 10%
        else: # Supply is sufficient, try to bid more conservatively
            # Bid slightly above average or just below fair price, but ensure it's competitive
            current_bid = max(current_bid, min(fair_price_per_unit * 0.9, avg_prev_bid + (fair_price_per_unit * 0.02)))
            # If highest bid was low, maybe I can bid even lower
            if highest_prev_bid < fair_price_per_unit * 0.7:
                current_bid = min(current_bid, highest_prev_bid + (fair_price_per_unit * 0.01))
    else: # No previous bids available for alive opponents (e.g., first day or all opponents are new/died)
        # Use a moderate bid based on supply/demand
        if total_water_demand > supply:
            current_bid = fair_price_per_unit * 1.05 # Slightly above fair
        else:
            current_bid = fair_price_per_unit * 0.8 # Conservative

    # Ensure bid is at least a minimal amount to get water if possible
    # This acts as a floor for bidding, preventing bidding too low when water is needed
    current_bid = max(current_bid, fair_price_per_unit * 0.4) 

    # Final check: Cap the bid by my maximum affordable bid
    return min(max_affordable_bid_per_unit, current_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    current_day = day_context['day']
    current_supply = day_context['supply']

    # Base bid for general competition
    base_bid = DAILY_SALARY * 0.5 # Default: 75

    # Scenario 1: No active opponents
    if not alive_opponents:
        # If I'm the only one left, bid minimally to secure water.
        # No need to bid high, even if HP is low, as there's no competition.
        return max(1.0, min(my_status['budget'], DAILY_SALARY * 0.1)) # Bid 15 or budget, minimum 1.0

    # Scenario 2: Survival mode (low HP or no water days)
    # This takes precedence over normal bidding as survival is key.
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        # Bid very high to ensure survival against active opponents.
        return min(my_status['budget'], DAILY_SALARY * 0.95) # 142.5 or budget

    # Scenario 3: Normal Bidding with active opponents
    
    # Adjust base bid based on remaining days and current budget
    remaining_days = EPISODE_DAYS - current_day + 1
    if remaining_days > 0:
        # If budget is tight for the remaining days, be more conservative.
        # A rough estimate of "needed" budget per day for average survival.
        avg_cost_per_day = DAILY_SALARY * 0.5 # Assuming I target to spend half my salary on average
        if my_status['budget'] / remaining_days < avg_cost_per_day * 0.8: 
            base_bid *= 0.85 # Be more conservative
        elif my_status['budget'] / remaining_days > avg_cost_per_day * 1.2: 
            base_bid *= 1.1 # Be more aggressive

    # Adjust for day progression: Bids tend to increase towards the end of the episode
    # This factor increases from 0 (Day 1) to 1 (Day 10)
    day_factor = (current_day - 1) / (EPISODE_DAYS - 1) if EPISODE_DAYS > 1 else 0
    base_bid += day_factor * (DAILY_SALARY * 0.2) # Adds up to 30 to base_bid as days progress

    # Adjust for supply scarcity: Higher competition when supply is low
    # supply_pressure is 1 if current_supply is MIN_SUPPLY, 0 if MAX_SUPPLY
    supply_pressure = 1 - (current_supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    base_bid += supply_pressure * (DAILY_SALARY * 0.15) # Adds up to 22.5 for low supply

    # Opponent reaction based on previous day's bids
    yesterday_opp_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_opp_bids.append(prev_trace['bid'])

    my_bid = base_bid

    if yesterday_opp_bids:
        max_opp_yesterday_bid = max(yesterday_opp_bids)
        # Bid slightly above the highest opponent bid from yesterday to be competitive
        # But only if it's higher than my calculated base_bid
        my_bid = max(my_bid, max_opp_yesterday_bid + 1.0)

    # Final bid capping and floor
    # Ensure bid doesn't exceed budget or a reasonable maximum for normal play
    max_reasonable_bid = DAILY_SALARY * 0.85 # 127.5
    my_bid = min(my_status['budget'], my_bid, max_reasonable_bid)

    # Ensure bid is at least 1.0 to participate
    my_bid = max(1.0, my_bid)

    return my_bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_HP = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    base_bid = 0.0
    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 1.05
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 7:
        base_bid = DAILY_SALARY * 0.75
    else:
        base_bid = DAILY_SALARY * 0.6

    if day_context['supply'] < WATER_REQ * 1.5:
        base_bid *= 1.15
    elif day_context['supply'] >= WATER_REQ * 2:
        base_bid *= 0.9

    strong_opponent_last_bids = []
    for opp_id, opp_data in opponents_status.items():
        if opp_id in ["Alex", "David"] and opp_data['alive']:
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                strong_opponent_last_bids.append(prev_trace['bid'])

    if strong_opponent_last_bids:
        max_strong_yesterday_bid = max(strong_opponent_last_bids)
        if my_status['hp'] < MAX_HP and base_bid < max_strong_yesterday_bid * 0.95:
            aggressive_bid_target = max_strong_yesterday_bid * 1.05
            base_bid = max(base_bid, min(aggressive_bid_target, DAILY_SALARY * 1.1))
        elif my_status['hp'] == MAX_HP and base_bid < max_strong_yesterday_bid * 0.8:
            base_bid = max(base_bid, max_strong_yesterday_bid * 0.85)

    final_bid = max(1.0, min(my_status['budget'], base_bid))

    return final_bid
"""
