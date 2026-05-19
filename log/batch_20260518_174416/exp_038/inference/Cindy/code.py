# ============================================================
# Experiment: exp_038
# Agent: Cindy
# Source: exp_038
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state, assuming it's constant for the meta-round

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimal to get water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # --- Bidding based on my HP --- 

    # Critical HP: Bid very aggressively
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # Low HP: Bid aggressively
    if my_status['hp'] == 3:
        return min(my_status['budget'], DAILY_SALARY * 0.75)

    # Healthy HP (my_status['hp'] > 3):
    current_supply = day_context['supply']
    current_day = day_context['day']

    # Calculate total water requirements from all active players
    total_water_demand = WATER_REQ
    for opp in alive_opponents:
        total_water_demand += opp['water_requirement']
    
    bid_amount = DAILY_SALARY * 0.5 # Default moderate bid

    # Adjust bid based on supply vs. total demand
    if current_supply < total_water_demand:
        # Supply is scarce, competition is high
        # Increase bid, but not to critical levels
        scarcity_multiplier = min(1.5, total_water_demand / current_supply) # Cap multiplier
        bid_amount = DAILY_SALARY * 0.55 * scarcity_multiplier
    else:
        # Supply is abundant or sufficient
        # Decrease bid to save budget
        bid_amount = DAILY_SALARY * 0.4

    # Adjust for end game
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last 2 days
        bid_amount = max(bid_amount, DAILY_SALARY * 0.7) # Ensure a strong bid
        bid_amount = min(bid_amount, DAILY_SALARY * 0.9) # Cap it

    # Ensure bid is within budget and has a reasonable floor
    final_bid = min(my_status['budget'], max(DAILY_SALARY * 0.15, bid_amount))
    
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
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    base_bid = DAILY_SALARY * 0.65 

    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        base_bid = DAILY_SALARY * 1.05 
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.85
    
    day_factor = (day_context['day'] / EPISODE_DAYS)
    base_bid += base_bid * 0.2 * day_factor 

    yesterday_bids = []
    opponent_water_requirements = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
        opponent_water_requirements.append(opp['water_requirement'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    if highest_prev_bid > DAILY_SALARY * 0.7:
        base_bid = max(base_bid, highest_prev_bid + 5)
    elif highest_prev_bid > 0:
        base_bid = max(base_bid, highest_prev_bid + 1)

    min_opp_req = WATER_REQ # Default if no opponents or requirements are found
    if opponent_water_requirements:
        min_opp_req = min(opponent_water_requirements)

    supply_for_me_and_one_opponent = WATER_REQ + min_opp_req

    if day_context['supply'] < WATER_REQ:
        if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
            base_bid = max(base_bid, DAILY_SALARY * 1.2)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.75)
    elif day_context['supply'] < supply_for_me_and_one_opponent:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif day_context['supply'] >= WATER_REQ * 2 and len(alive_opponents) < 2:
        base_bid = min(base_bid, DAILY_SALARY * 0.5)

    final_bid = max(0.0, base_bid)
    final_bid = min(my_status['budget'], final_bid)

    if final_bid == 0 and my_status['budget'] > 0 and (my_status['hp'] <= 5 or my_status['no_water_days'] > 0):
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.2) 

    if final_bid == 0 and my_status['budget'] > 0 and len(alive_opponents) > 0:
         final_bid = min(my_status['budget'], 1.0) 

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid factor, adjusted by remaining days and my HP
    base_bid_factor = 0.65 
    
    # Adjust for remaining days - become more aggressive towards the end
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 3:
        base_bid_factor = max(base_bid_factor, 0.8)
    
    # Adjust for HP - become very aggressive if low on HP
    if my_hp <= 3:
        base_bid_factor = 0.95 
    elif my_hp <= 5:
        base_bid_factor = max(base_bid_factor, 0.85)
    
    # If no opponents, bid minimum to win
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Analyze opponent bids from yesterday
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Initialize target bid based on calculated base factor
    target_bid = DAILY_SALARY * base_bid_factor

    if highest_prev_bid > 0:
        # If opponents are bidding high, I need to be competitive
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            target_bid = max(target_bid, highest_prev_bid + 5)
        else:
            target_bid = max(target_bid, highest_prev_bid + 2)
    
    # Consider supply vs demand
    # Total water requirement for all alive agents (including myself)
    total_water_demand = WATER_REQ * (num_alive_opponents + 1)
    
    # If supply is very tight, bid higher
    if current_supply < total_water_demand * 1.2:
        target_bid = max(target_bid, DAILY_SALARY * 0.8)
    
    # If supply is abundant, try to bid lower if possible
    if current_supply > total_water_demand * 1.5 and my_hp > 5:
        target_bid = min(target_bid, DAILY_SALARY * 0.7)

    # Cap the bid at daily salary (or slightly above if desperate and budget allows)
    # But ensure it's within budget
    final_bid = min(my_budget, target_bid)
    
    # Final check for critical HP or missed water - prioritize survival
    if my_hp <= 2:
        final_bid = min(my_budget, DAILY_SALARY * 0.99)
    elif my_no_water_days >= 1:
        final_bid = min(my_budget, DAILY_SALARY * 0.9)
    
    # Ensure bid is at least a minimal amount to indicate participation
    final_bid = max(final_bid, 1.0)

    return final_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    target_bid = DAILY_SALARY * 0.7 # Default aggressive bid

    if my_status['hp'] <= 2:
        target_bid = DAILY_SALARY * 0.99
    elif my_status['no_water_days'] >= 1:
        target_bid = DAILY_SALARY * 0.90
    elif my_status['hp'] <= 4:
        target_bid = DAILY_SALARY * 0.80

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if my_status['hp'] <= 4 or my_status['no_water_days'] >= 1:
            bid_to_beat = highest_prev_bid + 2.0
            target_bid = max(target_bid, bid_to_beat)
            if my_status['hp'] > 1:
                 target_bid = min(target_bid, DAILY_SALARY * 1.0)
        else:
            if highest_prev_bid > DAILY_SALARY * 0.7:
                target_bid = max(target_bid, highest_prev_bid * 1.01)
                target_bid = min(target_bid, DAILY_SALARY * 0.9)
            else:
                target_bid = max(target_bid, highest_prev_bid + 5.0)
                target_bid = min(target_bid, DAILY_SALARY * 0.75)

    if not yesterday_bids and day_context['day'] == 1:
        target_bid = DAILY_SALARY * 0.75

    final_bid = min(my_status['budget'], target_bid)

    if final_bid < 1.0 and my_status['budget'] > 0:
        return min(my_status['budget'], 1.0)

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
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

    # Emergency bid if HP is critical (3 days without water, HP=4)
    if my_status['hp'] <= 4:
        return min(my_status['budget'], DAILY_SALARY * 0.99) # Bid almost full salary

    # Analyze yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid
    # Starting base bid is aggressive due to tight supply and strong opponents (Alex, Eric)
    base_bid = DAILY_SALARY * 0.85 # Start with 127.5

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # React to yesterday's highest bid to stay competitive
        if highest_prev_bid >= DAILY_SALARY * 0.8: # If highest bid was 120 or more
            base_bid = max(base_bid, highest_prev_bid + 3) # Slightly outbid
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # If highest bid was 90 or more
            base_bid = max(base_bid, highest_prev_bid + 1) # Small increment
        else: # If yesterday's bids were surprisingly low, maintain a strong base
            base_bid = max(base_bid, DAILY_SALARY * 0.75) # Don't drop too low

    # Adjust bid based on my current HP (non-critical range)
    if my_status['hp'] < 8: # If I've missed at least one day of water (HP=8 or less)
        base_bid *= 1.05 # Be more aggressive
    elif my_status['hp'] >= 10: # If full HP, can be slightly less aggressive
        base_bid *= 0.98

    # Adjust based on supply (always tight, but some days are tighter)
    if day_context['supply'] <= MIN_SUPPLY + 2: # Supply 15, 16, 17
        base_bid *= 1.05 # Increase bid
    elif day_context['supply'] >= MAX_SUPPLY - 2: # Supply 23, 24, 25
        base_bid *= 0.95 # Slightly decrease bid

    # Ensure bid is within budget and has a reasonable minimum
    final_bid = min(my_status['budget'], max(DAILY_SALARY * 0.1, base_bid))
    
    # Cap the bid to prevent overspending too much beyond daily salary, unless critical HP
    final_bid = min(final_bid, DAILY_SALARY * 1.1) # Max 165

    # Final check for critical HP, overriding previous logic
    if my_status['hp'] <= 4:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.99)
    elif my_status['hp'] <= 6: # If 2 days without water, HP=6, still very dangerous
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.95) # High bid, but slightly less than critical

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to get water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Get yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid
    base_bid = DAILY_SALARY * 0.6

    # Adjust base bid based on supply
    # Lower supply means more competition, higher bid
    # Higher supply means less competition, potentially lower bid
    supply_normalized = (day_context['supply'] - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_impact_factor = 1 + (1 - supply_normalized) * 0.2 # Ranges from 1.0 (max supply) to 1.2 (min supply)
    base_bid *= supply_impact_factor

    # Adjust based on my HP
    if my_status['hp'] <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95 # Very aggressive
    elif my_status['hp'] <= 4: # Low HP
        base_bid = max(base_bid, DAILY_SALARY * 0.8) # Aggressive, ensure it's at least 0.8*salary
    elif my_status['hp'] <= 6: # Medium HP
        base_bid = max(base_bid, DAILY_SALARY * 0.7) # Moderate-aggressive
    else: # Healthy HP
        base_bid = max(base_bid, DAILY_SALARY * 0.5) # Can be less aggressive

    # Adjust based on opponent's yesterday's highest bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were aggressive, I need to be more aggressive, especially if my HP is not great
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents were very aggressive
            if my_status['hp'] <= 4:
                base_bid = max(base_bid, highest_prev_bid + 5) # Try to outbid
            else:
                base_bid = max(base_bid, highest_prev_bid * 0.95) # Match but cautiously
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # Opponents were moderately aggressive
            base_bid = max(base_bid, highest_prev_bid + 1) # Slightly outbid
        else: # Opponents were passive
            base_bid = max(base_bid, highest_prev_bid * 1.1) # Bid a bit higher than them

    # Adjust for remaining days
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] <= 4: # End game desperation
        base_bid = max(base_bid, DAILY_SALARY * 0.9) # Be very aggressive to survive final days

    # Ensure bid doesn't exceed budget or is not negative
    final_bid = min(my_status['budget'], max(0.01, base_bid))

    # Round to 2 decimal places
    return round(final_bid, 2)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents left, bid minimally to secure water
    if not alive_opponents:
        return min(my_status['budget'], 0.01)

    # Identify strong opponents (Alex, Eric) from historical context
    strong_opponents_ids = ["Alex", "Eric"]
    
    # Collect yesterday's bids from all alive opponents, prioritizing strong ones
    yesterday_bids = []
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                # Prioritize bids from strong opponents, or give a slight discount to others
                if opp_id in strong_opponents_ids:
                    yesterday_bids.append(prev['bid'])
                else:
                    # For weaker opponents, their bids are less indicative of the winning threshold
                    yesterday_bids.append(prev['bid'] * 0.9) # Discount weak opponent bids slightly
                
    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid calculation
    if highest_prev_bid == 0:
        target_bid = DAILY_SALARY * 0.7 # Default competitive bid (~105)
    else:
        target_bid = highest_prev_bid + 1.0 # Try to outbid yesterday's highest

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP: bid very aggressively
        bid = DAILY_SALARY * 0.98 # Maximize chances to get water
    elif my_status['hp'] <= 4: # Low HP: bid aggressively
        bid = DAILY_SALARY * 0.9 # High chance bid
    elif my_status['hp'] <= 6 and day_context['day'] >= EPISODE_DAYS - 3: # Mid-low HP late game
        bid = DAILY_SALARY * 0.85
    else: # Healthy HP or early/mid game
        # If my HP is very good and it's not late game, I can afford to be slightly less aggressive
        if my_status['hp'] > 10 and day_context['day'] < EPODE_DAYS / 2:
            bid = min(target_bid, DAILY_SALARY * 0.7) # Conserve, might lose but okay
        elif my_status['hp'] > 8: # Good HP, generally competitive
            bid = target_bid # Aim to win
            bid = min(bid, DAILY_SALARY * 0.85) # Cap at 85% of salary to avoid overspending
        else: # Moderate HP, need to be more aggressive
            bid = target_bid # Aim to win
            bid = min(bid, DAILY_SALARY * 0.9) # Cap at 90% of salary
        
        # Ensure a minimum competitive bid even if target_bid is low
        bid = max(bid, DAILY_SALARY * 0.6) # Minimum bid around 90

    # Ensure bid does not exceed available budget
    final_bid = min(my_status['budget'], bid)
    
    # Ensure bid is at least 0.01 (or some minimal amount)
    final_bid = max(0.01, final_bid)

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

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.6

    if my_hp <= 2: 
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4: 
        base_bid = DAILY_SALARY * 0.8
    elif my_hp >= 8: 
        base_bid = DAILY_SALARY * 0.45
    
    if my_no_water_days > 0:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.8: 
            if my_hp <= 3: 
                base_bid = max(base_bid, highest_prev_bid + 5)
            else: 
                base_bid = max(base_bid, highest_prev_bid * 1.01)
        elif highest_prev_bid < DAILY_SALARY * 0.4: 
            base_bid = min(base_bid, highest_prev_bid + 1)
        else: 
            base_bid = max(base_bid, highest_prev_bid * 1.01)

    days_remaining = EPISODE_DAYS - current_day + 1
    if days_remaining <= 3: 
        if my_hp <= 3:
            base_bid = max(base_bid, DAILY_SALARY * 1.0) 
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.85)
    elif days_remaining <= 5: 
        base_bid *= 1.1 

    final_bid = max(0.0, min(my_budget, base_bid))
    
    if my_budget < DAILY_SALARY * 0.5 and my_hp <= 2:
        final_bid = my_budget

    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQ = 13
    MY_DAILY_SALARY = 150
    EPISODE_DAYS = 10 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid a minimal amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], MY_DAILY_SALARY * 0.4)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    max_prev_bid = 0.0 # Initialize as float
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)

    # Determine target bid
    # Scenario: Only one agent can get their full water requirement (13 units)
    # given supply range [15, 25]. This implies extreme competition.
    # The highest bidder wins the water.

    if my_status['hp'] <= 3 or my_status['no_water_days'] > 0:
        # Critical condition: Must get water. Bid very aggressively.
        base_aggressive_bid = MY_DAILY_SALARY * 0.95 
        
        # If it's the last day or I'm in dire straits (very low HP), go more aggressive
        if day_context['day'] >= EPISODE_DAYS - 1 or my_status['hp'] <= 1:
            base_aggressive_bid = MY_DAILY_SALARY * 1.1 # Bid above salary if budget allows
        
        target_bid = max(base_aggressive_bid, max_prev_bid + 5)
            
    else:
        # Good HP: Still need to win, but can be slightly less aggressive to save budget.
        base_conservative_bid = MY_DAILY_SALARY * 0.8 
        
        target_bid = max(base_conservative_bid, max_prev_bid + 1)

    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], target_bid)
    
    # Ensure bid is at least 1 if budget allows and I need to participate
    # If budget is 0, bid 0. Otherwise, if calculated bid is 0 but budget > 0, bid 1.
    if final_bid <= 0 and my_status['budget'] > 0:
        final_bid = 1.0 
    elif final_bid < 0: # Ensure no negative bids if for some reason target_bid was negative
        final_bid = 0.0

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    yesterday_bids = []
    strong_opponents_bids = [] 
    
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
                if opp_id in ["David", "Eric"]:
                    strong_opponents_bids.append(prev['bid'])

    bid_amount = DAILY_SALARY * 0.5 

    if my_hp <= 2:
        bid_amount = DAILY_SALARY * 0.95
    elif my_hp <= 4:
        bid_amount = DAILY_SALARY * 0.8
    elif my_hp >= 8:
        bid_amount = DAILY_SALARY * 0.4

    if current_supply < WATER_REQ + 5:
        bid_amount *= 1.2
    elif current_supply > WATER_REQ + 10:
        bid_amount *= 0.8
        
    if strong_opponents_bids:
        max_strong_bid = max(strong_opponents_bids)
        
        if max_strong_bid >= DAILY_SALARY * 0.8:
            if my_hp <= 3 or current_supply <= WATER_REQ + 2:
                bid_amount = max(bid_amount, max_strong_bid + 5)
            else:
                bid_amount = max(bid_amount, max_strong_bid * 1.02)
        elif max_strong_bid >= DAILY_SALARY * 0.5:
            bid_amount = max(bid_amount, max_strong_bid * 1.01)

    elif yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        if max_yesterday_bid >= DAILY_SALARY * 0.6:
            bid_amount = max(bid_amount, max_yesterday_bid + 2)
        elif max_yesterday_bid >= DAILY_SALARY * 0.3:
            bid_amount = max(bid_amount, max_yesterday_bid * 1.05)
        else:
            bid_amount = min(bid_amount, DAILY_SALARY * 0.3)

    final_bid = bid_amount
    
    min_competitive_bid = DAILY_SALARY * 0.2 
    final_bid = max(min_competitive_bid, final_bid)

    final_bid = min(my_budget, final_bid)

    final_bid = max(0.01, final_bid)
    
    return final_bid
"""
