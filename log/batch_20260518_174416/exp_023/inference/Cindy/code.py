# ============================================================
# Experiment: exp_023
# Agent: Cindy
# Source: exp_023
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

    if num_alive_opponents == 0:
        return min(my_status['budget'], WATER_REQ * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_bid = DAILY_SALARY * 0.55

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 3:
                current_bid = DAILY_SALARY * 0.65
            else:
                current_bid = DAILY_SALARY * 0.95
        else:
            current_bid = max(current_bid, highest_prev_bid + 2.0)
    else:
        if my_status['hp'] <= 2:
            current_bid = DAILY_SALARY * 0.9
        elif my_status['hp'] <= 4:
            current_bid = DAILY_SALARY * 0.7
        else:
            current_bid = DAILY_SALARY * 0.55

    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        current_bid = DAILY_SALARY * 0.98

    final_bid = min(my_status['budget'], current_bid)
    final_bid = max(final_bid, WATER_REQ * 0.1) 

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        if day_context['supply'] >= WATER_REQ:
            return min(my_status['budget'], DAILY_SALARY * 0.1)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.05)

    current_bid = DAILY_SALARY * 0.5

    if my_status['hp'] <= 1:
        current_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 3:
        current_bid = DAILY_SALARY * 0.75
    elif my_status['hp'] <= 5:
        current_bid = DAILY_SALARY * 0.6

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] <= 3:
                current_bid = max(current_bid, highest_prev_bid + 5.0)
            else:
                current_bid = max(current_bid, highest_prev_bid * 0.9)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            current_bid = max(current_bid, average_prev_bid + 2.0)
        else:
            if my_status['hp'] > 5 and day_context['supply'] > WATER_REQ * num_alive_opponents:
                current_bid = min(current_bid, highest_prev_bid + 1.0)
            else:
                current_bid = max(current_bid, DAILY_SALARY * 0.3)

    total_water_needed = WATER_REQ
    for opp in alive_opponents:
        total_water_needed += opp['water_requirement']

    if day_context['supply'] < total_water_needed * 0.8:
        current_bid *= 1.15
    elif day_context['supply'] > total_water_needed * 1.2:
        current_bid *= 0.9

    if day_context['day'] >= EPISODE_DAYS * 0.7:
        current_bid *= 1.1

    final_bid = max(1.0, current_bid)
    final_bid = min(final_bid, my_status['budget'])

    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

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
        
        # Bidding strategy when there's previous opponent bid data
        if highest_prev_bid >= DAILY_SALARY * 0.85: # High competition threshold
            if my_status['hp'] > 3: # If healthy, conserve
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            else: # If low HP, bid aggressively to survive
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else: # Moderate competition
            # If my HP is low, be more aggressive than standard competitive bid
            if my_status['hp'] <= 2:
                return min(my_status['budget'], DAILY_SALARY * 0.9)
            # Otherwise, bid competitively but not excessively
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
    else:
        # Fallback strategy for Day 1 or if no opponent bid data available
        if my_status['hp'] <= 2: # If low HP, bid high to survive
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        else: # Otherwise, bid a moderate amount
            return min(my_status['budget'], DAILY_SALARY * 0.55)
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to survive
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    days_remaining = EPISODE_DAYS - current_day + 1
    if days_remaining <= 0:
        days_remaining = 1

    highest_prev_bid = 0.0
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Calculate my potential daily spend capacity
    my_potential_daily_spend = my_budget / days_remaining

    # Calculate average opponent daily spend capacity
    total_opponent_daily_capacity = 0.0
    num_competitive_opponents = 0
    for opp in alive_opponents:
        opp_days_remaining = EPISODE_DAYS - current_day + 1
        if opp_days_remaining <= 0: opp_days_remaining = 1
        opp_avg_daily_spend = opp['budget'] / opp_days_remaining
        if opp_avg_daily_spend > DAILY_SALARY * 0.05 and opp['hp'] > 0:
            total_opponent_daily_capacity += opp_avg_daily_spend
            num_competitive_opponents += 1

    avg_opponent_daily_capacity = 0.0
    if num_competitive_opponents > 0:
        avg_opponent_daily_capacity = total_opponent_daily_capacity / num_competitive_opponents

    bid_value = 0.0

    # High priority: survival
    if my_hp <= WATER_REQ or my_no_water_days > 0:
        # Critical state, must win water
        bid_value = DAILY_SALARY * 0.95 
        if highest_prev_bid > 0:
            bid_value = max(bid_value, highest_prev_bid + 5.0) 
    elif current_day >= EPISODE_DAYS - 2: 
        # End game, push for win
        bid_value = DAILY_SALARY * 0.85
        if highest_prev_bid > 0:
            bid_value = max(bid_value, highest_prev_bid + 3.0)
    else:
        # Normal state, try to save money but still compete
        bid_value = DAILY_SALARY * 0.6
        if highest_prev_bid > 0:
            if my_hp > WATER_REQ * 2 and my_potential_daily_spend > avg_opponent_daily_capacity * 1.5: 
                # Good HP and budget advantage, can try to outspend more aggressively
                bid_value = max(DAILY_SALARY * 0.65, highest_prev_bid + 8.0)
            elif my_hp > WATER_REQ * 1.5: 
                # Moderate HP, try to win but don't overspend too much
                bid_value = max(DAILY_SALARY * 0.55, highest_prev_bid + 2.0)
            else:
                # Somewhat low HP, need to be more competitive
                bid_value = max(DAILY_SALARY * 0.7, highest_prev_bid + 4.0)

    # Ensure bid is within budget and positive
    final_bid = max(1.0, min(bid_value, my_budget))

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
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Base bid strategy
    bid = DAILY_SALARY * 0.9 

    # HP-based aggression
    if my_status['hp'] <= 2: 
        bid = DAILY_SALARY * 1.4
    elif my_status['hp'] <= 4: 
        bid = DAILY_SALARY * 1.1
    elif my_status['hp'] >= 8: 
        bid = DAILY_SALARY * 0.8
    
    # Opponent reaction based on previous day's bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid > DAILY_SALARY * 1.1:
            if my_status['hp'] <= 3:
                bid = max(bid, highest_prev_bid + 5)
            else:
                bid = max(bid, highest_prev_bid * 1.02)
        elif highest_prev_bid > DAILY_SALARY * 0.8:
            bid = max(bid, highest_prev_bid + 1)
        else:
            if my_status['hp'] <= 2:
                bid = max(bid, DAILY_SALARY * 1.2)
            else:
                bid = min(bid, DAILY_SALARY * 0.7)

    # Endgame aggression
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2:
        if my_status['hp'] <= 5:
            bid = max(bid, DAILY_SALARY * 1.6)
        else:
            bid = max(bid, DAILY_SALARY * 1.1)
    elif remaining_days == 1:
        if my_status['hp'] <= 7:
            bid = max(bid, DAILY_SALARY * 1.8)
        else:
            bid = max(bid, DAILY_SALARY * 1.2)

    # Ensure bid is not negative and within budget
    final_bid = min(my_status['budget'], bid)
    final_bid = max(0.0, final_bid)

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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # --- Phase 1: Critical Survival Bids ---
    # If I'm very low on HP or have missed water, bid aggressively to survive.
    if my_hp <= 2 or my_no_water_days >= 1:
        return min(my_budget, DAILY_SALARY * 1.1) # Bid 110% of salary if possible

    # If I'm the only one left, bid minimally
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1) # Bid 10% of salary

    # --- Phase 2: End Game Bids ---
    # Push harder in the final days if not in critical state
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        return min(my_budget, DAILY_SALARY * 0.95) # Bid 95% of salary

    # --- Phase 3: Normal Strategic Bids ---
    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and prev.get('status') != 'error':
            yesterday_bids.append(prev['bid'])

    # Base bid
    bid = DAILY_SALARY * 0.75 # Default competitive bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # React to high opponent bids
        if highest_prev_bid >= DAILY_SALARY * 0.9: # Opponent bid very high
            bid = max(bid, highest_prev_bid + 1.0) # Try to outbid
        elif highest_prev_bid >= DAILY_SALARY * 0.7: # Opponent bid competitively
            bid = max(bid, highest_prev_bid * 1.02) # Slightly higher
        # React to low opponent bids (if my HP is good, save budget)
        elif highest_prev_bid < DAILY_SALARY * 0.5 and my_hp > 5:
            bid = min(bid, highest_prev_bid + 5.0) # Bid slightly above to secure, but don't overspend

    # Adjust bid based on my current HP (non-critical)
    if my_hp <= 5:
        bid *= 1.05 # Increase bid slightly if HP is getting somewhat low

    # Adjust bid based on supply scarcity
    # If supply is tight for two agents (e.g., 15-18 for two 13-water agents)
    if current_supply <= WATER_REQ + 5 and num_alive_opponents >= 1:
        bid *= 1.1 # Increase bid due to scarcity
    # If supply is abundant (e.g., 23-25), can be slightly less aggressive if HP is good
    elif current_supply >= MAX_SUPPLY - 2 and my_hp > 5:
        bid *= 0.95 # Decrease bid slightly

    # Final bid constraints
    final_bid = min(my_budget, bid)
    final_bid = max(0.0, final_bid) # Bid cannot be negative

    # Ensure a minimum bid if I need water
    if my_hp < 10 or my_no_water_days > 0:
        final_bid = max(final_bid, DAILY_SALARY * 0.25)

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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid strategy based on HP and day
    base_bid_multiplier = 0.7 # Default moderate bid
    if my_hp <= 2:
        base_bid_multiplier = 0.95 # Desperate to survive
    elif my_hp <= 4:
        base_bid_multiplier = 0.85 # Low HP, need water
    elif current_day >= EPISODE_DAYS - 2 and my_hp >= 8:
        # Healthy towards the end, aim to secure a win/survival
        base_bid_multiplier = 0.9 # Aggressive to secure water
    
    my_bid = DAILY_SALARY * base_bid_multiplier

    # Adjust bid based on opponent's previous bids
    highest_yesterday_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_yesterday_bid = max(highest_yesterday_bid, prev['bid'])

    if highest_yesterday_bid > 0:
        if my_hp <= 3: # Very low HP, must outbid significantly
            my_bid = max(my_bid, highest_yesterday_bid * 1.05 + 2)
        else: # Healthy, try to outbid but don't overspend too much
            my_bid = max(my_bid, highest_yesterday_bid + 5)
    
    # Adjust bid based on supply scarcity
    # The supply range is 15-25. Lower supply means higher competition.
    if current_supply <= 17: # Very low supply
        my_bid *= 1.15
    elif current_supply <= 20: # Moderate low supply
        my_bid *= 1.05

    # Ensure bid is within budget
    my_bid = min(my_bid, my_budget)

    # Ensure bid is not too low if I desperately need water and have budget
    if my_hp <= 2 and my_budget >= DAILY_SALARY * 0.5:
        my_bid = max(my_bid, DAILY_SALARY * 0.9)
    elif my_hp <= 4 and my_budget >= DAILY_SALARY * 0.3:
        my_bid = max(my_bid, DAILY_SALARY * 0.7)
    
    # Ensure a minimum bid if budget allows to stay in contention
    if my_budget >= DAILY_SALARY * 0.1 and my_bid < DAILY_SALARY * 0.1:
        my_bid = max(my_bid, DAILY_SALARY * 0.1)
    elif my_budget < DAILY_SALARY * 0.1 and my_hp > 1: # If budget is almost gone, try to save a little
        my_bid = min(my_budget, DAILY_SALARY * 0.05)

    # Ensure bid is never negative
    my_bid = max(0.0, my_bid)

    return my_bid
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
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to secure water
    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    # Base bid - a starting point for the bid
    base_bid = DAILY_SALARY * 0.65

    # 1. Survival mode: If HP is critical or no water for too long, bid very high.
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        base_bid = DAILY_SALARY * 0.98 
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.85
    
    # 2. End-game strategy: If it's near the end of the episode, bid more aggressively if budget allows
    if day_context['day'] >= EPISODE_DAYS - 2: # Last two days
        if my_status['hp'] > 0: 
            base_bid = max(base_bid, DAILY_SALARY * 0.9)
            if my_status['budget'] > DAILY_SALARY * 2: # If rich, spend more to win
                base_bid = max(base_bid, my_status['budget'] * 0.5)

    # 3. Adapt to opponent's previous day bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents bid very high yesterday, I need to be competitive
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, highest_prev_bid * 1.05) 
        # If highest previous bid was moderate, adjust slightly
        elif highest_prev_bid >= DAILY_SALARY * 0.4:
            base_bid = max(base_bid, highest_prev_bid * 1.01) 
        # If bids were low, try to conserve, but not too low if I need water
        else:
            base_bid = min(base_bid, highest_prev_bid * 1.2)

    # 4. Adjust for supply vs. demand
    supply = day_context['supply']
    estimated_total_demand = (num_alive_opponents + 1) * WATER_REQ

    if supply < estimated_total_demand * 0.8: # Supply is low relative to demand, high competition
        base_bid *= 1.1 
    elif supply > estimated_total_demand * 1.2: # Supply is high, lower competition
        base_bid *= 0.9 

    # Final bid must be positive and not exceed current budget
    final_bid = max(0.1, min(my_status['budget'], base_bid))

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

    # 1. Initialize bid based on my value for water
    bid = DAILY_SALARY * 0.5 # Default baseline bid

    # If no opponents, bid a minimal amount to conserve budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1) # Bid 15

    # Analyze yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # 2. Adjust bid based on my HP (desperation factor)
    if my_status['hp'] <= 2: # Critical HP
        bid = DAILY_SALARY * 0.95 
    elif my_status['hp'] <= 4: # Low HP
        bid = DAILY_SALARY * 0.85 # 127.5
    elif my_status['hp'] <= 6: # Medium-low HP
        bid = DAILY_SALARY * 0.7 # 105

    # 3. Adjust bid based on supply and number of opponents (competition factor)
    supply = day_context['supply']
    num_possible_allocations = int(supply // WATER_REQ) 

    if num_possible_allocations == 0: # Supply less than my requirement
        # Always prioritize survival here, even if HP is high
        bid = max(bid, DAILY_SALARY * 0.8) # Ensure high bid in this scenario
        if my_status['hp'] <= 4:
            bid = max(bid, DAILY_SALARY * 0.98) 

    elif num_possible_allocations == 1: # Supply enough for one person
        if num_alive_opponents >= 2: # Me + 2 or more opponents fighting for 1 slot
            bid = max(bid, DAILY_SALARY * 0.8) # High base for fierce competition
            if my_status['hp'] <= 4:
                bid = max(bid, DAILY_SALARY * 0.9)
        elif num_alive_opponents == 1: # Me vs 1 opponent for 1 slot
            bid = max(bid, DAILY_SALARY * 0.65) # Moderate base
            if my_status['hp'] <= 4:
                bid = max(bid, DAILY_SALARY * 0.8)

    elif num_possible_allocations >= 2: # Supply enough for two or more
        if num_alive_opponents >= 2: # Multiple players, multiple slots
            bid = max(bid, DAILY_SALARY * 0.55) # Slightly above default
            if my_status['hp'] <= 4:
                bid = max(bid, DAILY_SALARY * 0.7)
        else: # Very low competition (e.g., me + one opponent, or just me)
            bid = max(bid, DAILY_SALARY * 0.3) # Can be more conservative

    # 4. Adjust bid to outcompete previous highest bid
    if highest_prev_bid > 0:
        # If my current calculated bid is lower than previous highest, try to exceed it
        if bid <= highest_prev_bid:
            bid = highest_prev_bid + 2.0 # Try to outbid by a small margin
        elif bid < highest_prev_bid + 5.0 and my_status['hp'] <= 4: # If already higher but not by much and desperate
            bid = highest_prev_bid + 5.0 # Be more aggressive

    # Cap the bid to avoid overpaying unnecessarily, but allow high bids when desperate
    if my_status['hp'] > 4: # If not desperate, cap bids
        bid = min(bid, DAILY_SALARY * 0.9) # Don't bid more than 90% of salary if not desperate
    else: # If desperate, allow bids up to almost full salary
        bid = min(bid, DAILY_SALARY * 0.99)

    # Ensure bid is at least slightly above 0 if there are opponents
    if bid < 5.0 and num_alive_opponents > 0:
        bid = 5.0

    # Final check: Don't bid more than I have
    final_bid = min(my_status['budget'], bid)
    
    # Ensure bid is not negative
    final_bid = max(0.0, final_bid)

    return float(final_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    days_left = EPISODE_DAYS - day_context['day']

    # Strategy 1: If no opponents, bid minimally
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Strategy 2: Critical HP - prioritize survival
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # Strategy 3: End of game - bid aggressively if needed
    if days_left == 0: # Last day
        return min(my_status['budget'], DAILY_SALARY * 0.9)

    # Strategy 4: Normal game play
    # Calculate a base bid influenced by supply scarcity
    # Higher supply -> lower base bid, Lower supply -> higher base bid
    supply_normalized = (day_context['supply'] - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    # Base bid ranges from 0.9*DAILY_SALARY (low supply) to 0.5*DAILY_SALARY (high supply)
    base_bid = DAILY_SALARY * (0.9 - supply_normalized * 0.4)

    # Collect yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_bid = base_bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Very high bids from opponents
            if my_status['hp'] > 5: # Good HP, try to match or slightly conserve
                current_bid = max(current_bid, highest_prev_bid * 0.95)
            else: # HP is medium, need to be aggressive
                current_bid = max(current_bid, highest_prev_bid * 1.05)
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # Moderate bids
            current_bid = max(current_bid, highest_prev_bid + 5)
        else: # Low bids
            current_bid = max(current_bid, highest_prev_bid * 1.1)

    final_bid = min(my_status['budget'], current_bid)
    
    return max(1.0, final_bid)
"""
