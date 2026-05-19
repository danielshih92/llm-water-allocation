# ============================================================
# Experiment: exp_027
# Agent: Cindy
# Source: exp_027
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

    # If no opponents, bid minimally to secure water
    if num_alive_opponents == 0:
        return int(min(my_status['budget'], 1))

    # Base bid strategy based on my HP
    bid_amount = 0.0 # Use float for calculations, convert to int at the end

    if my_status['hp'] <= 2: # Critical HP, must win
        bid_amount = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP, need water
        bid_amount = DAILY_SALARY * 0.8
    else: # Good HP, can be slightly less aggressive but still aim to win
        bid_amount = DAILY_SALARY * 0.65

    # Adjust bid based on opponent's previous behavior (if available)
    highest_prev_opp_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_opp_bid = max(highest_prev_opp_bid, float(prev['bid'])) # Ensure float comparison

    if highest_prev_opp_bid > 0:
        # If opponent was very aggressive yesterday, especially if I'm not in a great state
        if highest_prev_opp_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] <= 3: # I am also under pressure
                bid_amount = max(bid_amount, highest_prev_opp_bid + 5.0) # Try to outbid
            else: # I am in a better state, but still need to compete
                bid_amount = max(bid_amount, DAILY_SALARY * 0.75) # Ensure strong bid
        else: # Opponent bid moderately or low
            if my_status['hp'] <= 2: # I am desperate
                bid_amount = max(bid_amount, DAILY_SALARY * 0.9) # Keep high bid
            else: # I am okay, try to win efficiently
                bid_amount = max(bid_amount, highest_prev_opp_bid + 1.0) # Slightly higher than opponent

    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], bid_amount)

    # Ensure bid is at least 1 if I need water (and am alive)
    if final_bid < 1.0 and my_status['hp'] > 0:
        final_bid = min(my_status['budget'], 1.0)

    return int(final_bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    # Calculate total water demand from all alive agents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    total_opponent_water_req = sum(o['water_requirement'] for o in alive_opponents)
    total_demand = WATER_REQ + total_opponent_water_req

    # --- Bidding Logic ---

    # 1. Survival Mode: If HP is very low or water was missed, bid aggressively
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # 2. Analyze yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid
    base_bid = DAILY_SALARY * 0.55 # Moderate starting bid

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # Adjust bid based on opponent's previous aggression
        if max_prev_bid >= DAILY_SALARY * 0.8: # Very high bids yesterday
            base_bid = max(base_bid, DAILY_SALARY * 0.75) # Increase our bid significantly
        elif avg_prev_bid >= DAILY_SALARY * 0.6: # Moderately high average bids
            base_bid = max(base_bid, avg_prev_bid + 5.0) # Bid slightly above average
        else: # Generally low bids yesterday
            base_bid = max(base_bid, DAILY_SALARY * 0.4) # A bit lower to save money

    # 3. Adjust based on supply scarcity
    # If supply is less than total demand, competition is high
    if day_context['supply'] < total_demand:
        # Increase bid to compete for scarce resources
        base_bid = max(base_bid, DAILY_SALARY * 0.7) # Ensure we are competitive
        if my_status['hp'] <= 5: # More aggressive if HP is not great
             base_bid = max(base_bid, DAILY_SALARY * 0.85)
    elif day_context['supply'] >= total_demand + WATER_REQ * 2: # Abundant supply
        # Decrease bid if supply is very high, less competition
        base_bid = min(base_bid, DAILY_SALARY * 0.35) # Try to get it cheap
    
    # 4. Final bid calculation, ensuring it doesn't exceed budget and is at least 1
    final_bid = min(my_status['budget'], base_bid)
    
    return max(1.0, final_bid)
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    if my_hp <= 1 or my_no_water_days >= 1:
        return min(my_budget, DAILY_SALARY * 0.98)

    if current_day >= EPISODE_DAYS - 2 and my_hp <= 3:
        return min(my_budget, DAILY_SALARY * 0.95)

    yesterday_bids = []
    desperate_opponents_count = 0
    strong_opponents_count = 0

    for opp in alive_opponents:
        opp_water_req = opp.get('water_requirement', WATER_REQ)

        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
        
        if opp['hp'] <= opp_water_req / 2 or opp['no_water_days'] >= 2:
            desperate_opponents_count += 1
        
        if opp['budget'] > DAILY_SALARY * 2 and opp['hp'] > 5:
            strong_opponents_count += 1

    bid = DAILY_SALARY * 0.5

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            bid = max(bid, highest_prev_bid * 1.05)
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            bid = max(bid, highest_prev_bid + 5)
        else:
            bid = max(bid, highest_prev_bid * 1.1)
    
    if desperate_opponents_count > 0:
        bid = max(bid, DAILY_SALARY * 0.65 + desperate_opponents_count * 7)

    if strong_opponents_count > 0:
        bid = max(bid, DAILY_SALARY * 0.7 + strong_opponents_count * 10)

    if current_supply < WATER_REQ * 2 and current_supply >= WATER_REQ and num_alive_opponents > 0:
        bid = max(bid, DAILY_SALARY * 0.8)
    elif current_supply < WATER_REQ:
        if my_hp > 5 and current_day < EPISODE_DAYS - 2:
            bid = min(bid, DAILY_SALARY * 0.3)
        else:
            bid = max(bid, DAILY_SALARY * 0.7)

    if my_hp > 5 and current_day < EPISODE_DAYS - 3:
        bid = min(bid, DAILY_SALARY * 0.7)
    elif my_hp > 7 and current_day < EPISODE_DAYS - 5:
        bid = min(bid, DAILY_SALARY * 0.6)

    final_bid = min(my_budget, bid)
    final_bid = min(final_bid, DAILY_SALARY * 0.99)

    if final_bid < DAILY_SALARY * 0.15 and my_hp > 2:
        final_bid = DAILY_SALARY * 0.15

    if current_day == 1 and not yesterday_bids:
        final_bid = DAILY_SALARY * 0.7

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

    # Base bid
    bid = DAILY_SALARY * 0.5 # Default moderate bid

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP, must get water
        bid = DAILY_SALARY * 1.2
    elif my_status['hp'] <= 4: # Low HP, prioritize water
        bid = DAILY_SALARY * 0.9
    elif my_status['hp'] >= 8 and my_status['budget'] > DAILY_SALARY * 2: # Healthy and good budget, can be less aggressive
        bid = DAILY_SALARY * 0.35

    # Adjust bid based on supply
    # Supply range is [15, 25]. My water_requirement is 13.
    # At 15 supply, only one player can get water for 13 units. At 25 supply, still only one player can get full 13 units if others also need it.
    # This means supply is always scarce for two players to get full water_requirement simultaneously.
    if day_context['supply'] <= 16: # Very low supply, high competition
        bid = max(bid, DAILY_SALARY * 0.8)
    elif day_context['supply'] <= 20: # Medium-low supply
        bid = max(bid, DAILY_SALARY * 0.6)

    # Adjust bid based on opponent behavior from yesterday's trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents bid very high yesterday, I might need to counter
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] <= 4: # If I also need water, match or exceed
                bid = max(bid, highest_prev_bid + 5) # Slightly higher to win
            else: # If I'm healthy, maybe conserve a bit but still compete
                bid = max(bid, highest_prev_bid * 0.95) # Slightly less than highest, hoping they overbid or I get it cheaper
        elif highest_prev_bid < DAILY_SALARY * 0.3: # Opponents bid low, I can also bid lower if healthy
            if my_status['hp'] > 6:
                bid = min(bid, DAILY_SALARY * 0.3)

    # Adjust for day progression (end of episode)
    if day_context['day'] >= EPISODE_DAYS - 2: # Last few days, players get desperate
        bid = max(bid, DAILY_SALARY * 1.0) # Bid at least daily salary
        if my_status['hp'] <= 5: # Really need water to survive final days
            bid = max(bid, DAILY_SALARY * 1.5)

    # If no opponents are alive, bid minimum to conserve budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1) # Smallest bid to get water

    # Ensure bid is not negative and within budget
    final_bid = max(0.0, min(bid, my_status['budget']))

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ_CINDY = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid very low to save budget
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Base bid - a fraction of daily salary
    base_bid = DAILY_SALARY * 0.5

    # 1. Adjust bid based on my HP
    if my_hp <= 2: # Critical HP, bid aggressively
        base_bid = max(base_bid, DAILY_SALARY * 0.95)
    elif my_hp <= 4: # Low HP
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    elif my_hp >= 8: # High HP, can afford to save a bit
        base_bid = min(base_bid, DAILY_SALARY * 0.4)

    # 2. Adjust bid based on supply relative to potential demand
    # A simple heuristic: if supply is low relative to my requirement and number of competitors
    if current_supply < WATER_REQ_CINDY * 1.5: # Very low supply, high competition
        base_bid = max(base_bid, DAILY_SALARY * 0.85)
    elif current_supply < WATER_REQ_CINDY * (num_alive_opponents / 2 + 1): # Moderate supply, still competitive
        base_bid = max(base_bid, DAILY_SALARY * 0.65)
    else: # Higher supply, can afford to bid lower
        base_bid = min(base_bid, DAILY_SALARY * 0.4)

    # 3. Adjust bid based on opponents' yesterday bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents bid high yesterday, consider raising my bid to stay competitive
        if max_yesterday_bid > DAILY_SALARY * 0.7 and my_hp < 6: # Only react strongly if my HP isn't super high
            base_bid = max(base_bid, max_yesterday_bid * 1.05) # Slightly above max
        elif avg_yesterday_bid > DAILY_SALARY * 0.5:
            base_bid = max(base_bid, avg_yesterday_bid * 1.05) # Slightly above average
        # If opponents bid low yesterday and supply is not critical, consider lowering my bid
        elif avg_yesterday_bid < DAILY_SALARY * 0.4 and current_supply > WATER_REQ_CINDY * 2: # Only if supply is ample
            base_bid = min(base_bid, avg_yesterday_bid * 0.9)

    # 4. Adjust for end-game pressure
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last 2 days
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif remaining_days <= 4: # Last 4 days
        base_bid = max(base_bid, DAILY_SALARY * 0.7)

    # Ensure bid is not negative and within budget
    final_bid = max(0.0, base_bid)
    return min(my_budget, final_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    my_current_budget = my_status['budget']
    my_current_hp = my_status['hp']
    current_day = day_context['day']
    days_left = EPISODE_DAYS - current_day

    # Base bid: a solid default to stay competitive
    bid = DAILY_SALARY * 0.65 # Start with 97.5

    # Identify Alex and their last known bid
    alex_status = opponents_status.get('Alex')
    alex_last_bid = 0.0
    if alex_status and alex_status['alive'] and alex_status.get('previous_trace'):
        alex_last_bid = alex_status['previous_trace'].get('bid', 0.0)

    # Adjust bid based on Alex's previous aggressive behavior
    if alex_last_bid > 0:
        # If Alex bid very high, try to outbid them slightly more aggressively
        if alex_last_bid >= DAILY_SALARY * 0.9: # Alex bid 135 or more
            bid = max(bid, alex_last_bid + 1.5)
        elif alex_last_bid >= DAILY_SALARY * 0.7: # Alex bid 105 or more
            bid = max(bid, alex_last_bid + 1.0)
        else:
            # If Alex's bid was moderate, still try to beat it
            bid = max(bid, alex_last_bid + 0.5)

    # Adjust bid based on my current HP (survival priority)
    # If my current HP is less than WATER_REQ * days_left, I need water to survive.
    # Adding 1 to days_left checks if I need water *today* to survive all remaining days.
    if my_current_hp <= WATER_REQ * 0.5: # Critical HP (e.g., HP <= 6.5) - MUST win
        bid = max(bid, DAILY_SALARY * 0.99)
    elif my_current_hp <= WATER_REQ: # Low HP (e.g., HP <= 13) - High priority to win
        bid = max(bid, DAILY_SALARY * 0.9)
    elif my_current_hp <= WATER_REQ * 1.5 and alex_status and alex_status['alive']: # Moderate HP, Alex is a threat
        bid = max(bid, DAILY_SALARY * 0.8)

    # Adjust bid for end game scenario
    if days_left <= 2:
        # If I need water to survive the remaining days (including today)
        if my_current_hp < WATER_REQ * (days_left + 1):
             bid = max(bid, DAILY_SALARY * 0.99) # Bid very aggressively to survive
    elif days_left <= 4 and my_current_hp < WATER_REQ * (days_left + 1): # Mid-late game pressure
        bid = max(bid, DAILY_SALARY * 0.85)

    # Ensure bid does not exceed current budget
    bid = min(bid, my_current_budget)
    
    # Ensure a minimum bid if I have budget and need water, even if calculated bid is low
    # If current bid is very low and I have budget, but need water to potentially survive
    if bid < 10 and my_current_budget >= 10 and my_current_hp < WATER_REQ * (days_left + 2):
        bid = max(bid, DAILY_SALARY * 0.1)
    elif bid < 1 and my_current_budget >= 1:
        # If calculated bid is almost zero but budget allows a token bid
        bid = max(bid, 1.0)

    return float(bid)
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
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimum to win
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Critical observation: WATER_REQ=13, supply_range=[15, 25].
    # max_winners = int(current_supply / WATER_REQ) will always be 1.
    # This means only one agent can win water each day, making competition always fierce.

    # Base bid: Start aggressive due to constant fierce competition.
    base_bid = DAILY_SALARY * 0.7

    # Increase aggression if critical HP or no water days
    if my_hp <= 2 or my_no_water_days >= 1:
        base_bid = DAILY_SALARY * 0.95 # Very aggressive to survive
    elif my_hp <= 4:
        base_bid = DAILY_SALARY * 0.85 # Moderately aggressive

    # If it's late in the game, become more aggressive to finish strong
    if current_day >= EPISODE_DAYS - 2:
        if my_hp > 0: # Only if still alive and fighting
            base_bid = max(base_bid, DAILY_SALARY * 0.9) # Push hard at the end

    # Adjust based on opponent's yesterday bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    final_bid = base_bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Always try to beat the highest previous bid since only one winner
        # Adjust bid based on how high the previous bid was to avoid overspending too much
        if highest_prev_bid >= DAILY_SALARY * 0.9: # If opponents are bidding very high
            final_bid = max(final_bid, highest_prev_bid + 2) # Just slightly over, if budget allows
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # If opponents are bidding moderately high
            final_bid = max(final_bid, highest_prev_bid + 5)
        else: # If opponents are bidding low
            final_bid = max(final_bid, highest_prev_bid + 10) # More aggressive to secure win

    # Budget constraint: Cannot bid more than available budget
    final_bid = min(my_budget, final_bid)

    # Ensure a minimum bid to participate, unless budget is zero
    if my_budget > 0:
        if my_hp <= 2 or my_no_water_days >= 1: # If critical, bid a significant portion, up to budget
            final_bid = max(final_bid, min(my_budget, DAILY_SALARY * 0.9))
        else: # Normal state, ensure at least a moderate bid due to constant competition
            final_bid = max(final_bid, DAILY_SALARY * 0.2)
    else:
        final_bid = 0.0 # No budget, cannot bid

    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    current_supply = day_context['supply']

    base_bid = DAILY_SALARY * 0.55

    supply_factor = (current_supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    inverse_supply_factor = 1 - supply_factor
    
    base_bid += inverse_supply_factor * (DAILY_SALARY * 0.2)

    if my_current_hp <= 2:
        bid = DAILY_SALARY * 0.98
    elif my_current_hp <= 4:
        bid = DAILY_SALARY * 0.85
    elif my_current_hp <= 6:
        bid = DAILY_SALARY * 0.75
    else:
        bid = base_bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if my_current_hp > 4:
            bid = max(bid, highest_prev_bid + 5)
            bid = min(bid, DAILY_SALARY * 0.9)
        else:
            bid = max(bid, highest_prev_bid + 10)
            bid = min(bid, DAILY_SALARY * 0.99)

    bid = min(bid, my_current_budget)
    
    if bid < 1.0 and my_current_budget > 0:
        bid = 1.0
    
    return max(0.0, bid)
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
        if my_status['hp'] <= WATER_REQ:
            return min(my_status['budget'], DAILY_SALARY * 0.2)
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.55

    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.8

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 5 and my_status['budget'] > DAILY_SALARY * 3:
                base_bid = min(base_bid, DAILY_SALARY * 0.4)
            else:
                base_bid = max(base_bid, highest_prev_bid + 5)
                base_bid = min(base_bid, DAILY_SALARY * 1.0)

        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            if my_status['hp'] > 6:
                base_bid = max(base_bid, highest_prev_bid + 1.5)
            else:
                base_bid = max(base_bid, highest_prev_bid + 5)
            base_bid = min(base_bid, DAILY_SALARY * 0.9)

        else:
            if my_status['hp'] > 7:
                base_bid = min(base_bid, DAILY_SALARY * 0.3)
            else:
                base_bid = max(base_bid, DAILY_SALARY * 0.4)

    remaining_days = EPISODE_DAYS - day_context['day']
    estimated_cost_per_day = DAILY_SALARY * 0.5
    min_budget_needed_for_survival = remaining_days * estimated_cost_per_day

    if my_status['budget'] < min_budget_needed_for_survival * 1.2:
        if my_status['hp'] <= 3:
            base_bid = max(base_bid, DAILY_SALARY * 0.95)
        elif my_status['hp'] > 6:
            base_bid = min(base_bid, DAILY_SALARY * 0.4)

    final_bid = min(my_status['budget'], base_bid)

    if final_bid <= 0 and my_status['budget'] > 0:
        return 0.1
    elif final_bid <= 0:
        return 0

    return final_bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13
    EPISODE_DAYS = 10 # From meta_round_state

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    current_day = day_context['day']
    days_left = EPISODE_DAYS - current_day + 1

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid very low to save budget.
    if num_alive_opponents == 0:
        return int(min(my_current_budget, DAILY_SALARY * 0.1))

    # Analyze opponent's previous bids and current status
    highest_prev_bid = 0
    alex_hp = None
    alex_budget = None

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])
            
        if opp['agent_id'] == "Alex":
            alex_hp = opp['hp']
            alex_budget = opp['budget']

    # Determine my base bid based on HP and days left
    base_bid_value = DAILY_SALARY * 0.5 # Default conservative bid value
    
    if my_current_hp <= 2: # Very desperate
        base_bid_value = DAILY_SALARY * 0.95
    elif my_current_hp <= 4: # Desperate
        base_bid_value = DAILY_SALARY * 0.8
    elif my_current_hp <= 6: # Needs water
        base_bid_value = DAILY_SALARY * 0.65
    
    # Increase bid if it's late in the game, especially if I need water
    if days_left <= 3:
        if my_current_hp <= 4: # If low HP late game
            base_bid_value = max(base_bid_value, DAILY_SALARY * 0.9) # Be very aggressive
        elif my_current_hp <= 6: # If moderate HP late game
            base_bid_value = max(base_bid_value, DAILY_SALARY * 0.75) # Aggressive
        else: # If healthy late game, still need to compete
            base_bid_value = max(base_bid_value, DAILY_SALARY * 0.6) # Moderate aggressive

    # Now, combine with opponent's previous highest bid to ensure competitiveness
    my_calculated_bid = base_bid_value
    if highest_prev_bid > 0:
        if my_current_hp <= 4: # If desperate, bid significantly higher than previous max
            my_calculated_bid = max(my_calculated_bid, highest_prev_bid + 3)
        else: # If healthy, bid slightly higher to stay competitive
            my_calculated_bid = max(my_calculated_bid, highest_prev_bid + 1)

    # Specific exploit: If Alex is very desperate (low HP) and has high budget, and I'm healthy and it's not endgame,
    # let him spend his money. This is a strategic retreat to conserve my budget.
    if (alex_hp is not None and alex_hp <= 2 and 
        alex_budget is not None and alex_budget > DAILY_SALARY * 0.8 and 
        my_current_hp > 6 and days_left > 3):
        my_calculated_bid = min(my_calculated_bid, DAILY_SALARY * 0.5) # Conserve budget by bidding lower

    # Ensure bid doesn't exceed my budget
    final_bid = min(my_current_budget, my_calculated_bid)

    # Absolute last resort: if about to die, bid everything
    if my_current_hp <= 1 and my_current_budget > 0:
        return int(my_current_budget)
    
    return int(final_bid)
"""
