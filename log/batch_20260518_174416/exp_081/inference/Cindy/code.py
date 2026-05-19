# ============================================================
# Experiment: exp_081
# Agent: Cindy
# Source: exp_081
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    # 1. Prioritize survival
    # If HP is critical (2 or less) or I missed water yesterday, bid aggressively
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        return min(my_status['budget'], DAILY_SALARY * 0.95) # Very high bid to secure water

    # 2. Analyze opponents' previous bids and current supply
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)
    current_supply = day_context['supply']

    highest_opp_prev_bid = 0
    total_opp_prev_bids = 0
    num_opponents_with_trace = 0

    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            highest_opp_prev_bid = max(highest_opp_prev_bid, prev_trace['bid'])
            total_opp_prev_bids += prev_trace['bid']
            num_opponents_with_trace += 1

    avg_opp_prev_bid = total_opp_prev_bids / num_opponents_with_trace if num_opponents_with_trace > 0 else 0

    # Calculate available water slots, explicitly casting to int for indexing safety if used as such
    slots_available = int(current_supply // WATER_REQ)

    # 3. Determine base bid based on supply scarcity and opponent behavior
    target_bid = DAILY_SALARY * 0.5 # Default moderate bid

    if slots_available >= num_alive_opponents + 1: # Abundant supply for everyone
        target_bid = DAILY_SALARY * 0.3 # Conservative bid
        if avg_opp_prev_bid > 0:
            # If opponents overbid yesterday, try to get it cheaper by undercutting slightly
            target_bid = min(target_bid, avg_opp_prev_bid * 0.9)
    elif slots_available >= 1: # Limited supply, but possible to get water
        target_bid = DAILY_SALARY * 0.6 # Moderate to competitive bid
        if highest_opp_prev_bid > 0:
            # If opponents bid high, be competitive by bidding slightly higher
            target_bid = max(target_bid, highest_opp_prev_bid + 5)
    else: # Very scarce supply, highly competitive or impossible to get water
        target_bid = DAILY_SALARY * 0.8 # Aggressive bid
        if highest_opp_prev_bid > 0:
            # Be very aggressive if opponents bid high to try and secure the single slot
            target_bid = max(target_bid, highest_opp_prev_bid + 10)
        
    # Ensure bid does not exceed budget and is at least 1
    final_bid = min(target_bid, my_status['budget'])
    final_bid = max(final_bid, 1)

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

    # If no opponents are alive, bid minimum to conserve budget.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    num_active_players = len(alive_opponents) + 1 # Including myself

    # --- 1. Desperation Mode (My HP is critical or I missed water) ---
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        # Bid very aggressively to survive. Almost full salary.
        return min(my_status['budget'], DAILY_SALARY * 0.98)

    # --- 2. Analyze Opponent Yesterday's Bids and Current Status ---
    highest_prev_bid = 0.0
    opponent_desperate_status_count = 0 # Count how many opponents are desperate
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])
            # If opponent failed to get water yesterday and is low on HP
            if prev.get('status') == 'no_water' and prev.get('hp_after', 100) <= 3:
                opponent_desperate_status_count += 1
        # Also check if they are currently very low on HP
        if opp['hp'] <= 3:
            opponent_desperate_status_count += 1

    # --- 3. Calculate Base Bid ---
    # Base bid scaled by water requirement vs supply.
    # If supply is low, the effective price per unit of water increases.
    # Ensure a minimum bid to stay competitive (e.g., 55% of salary).
    base_bid = DAILY_SALARY * (WATER_REQ / day_context['supply'])
    base_bid = max(base_bid, DAILY_SALARY * 0.55)

    # --- 4. Adjust Bid based on Opponent Behavior and Game State ---
    current_bid = base_bid

    # If opponents are desperate, assume high bids from them.
    if opponent_desperate_status_count > 0:
        current_bid = max(current_bid, DAILY_SALARY * 0.9) # Be very aggressive
        if highest_prev_bid > 0:
            current_bid = max(current_bid, highest_prev_bid + 5.0) # Try to outbid previous high

    elif highest_prev_bid > 0:
        # If highest previous bid was significant, try to beat it slightly.
        if my_status['hp'] > 5: # Healthy
            current_bid = max(current_bid, highest_prev_bid + 1.5)
            # If highest_prev_bid is very high, cap my bid but ensure it's still competitive
            if highest_prev_bid > DAILY_SALARY * 0.9:
                current_bid = min(current_bid, DAILY_SALARY * 0.95)
                current_bid = max(current_bid, highest_prev_bid + 0.5) # Ensure it's still above
        else: # Moderately low HP, need water more, be more aggressive
            current_bid = max(current_bid, highest_prev_bid + 3.0)

    # --- 5. Further Adjustments for Game Phase and Supply Scarcity ---
    remaining_days = EPISODE_DAYS - day_context['day']

    # If supply is very tight (e.g., barely enough for one player) and multiple players are active,
    # competition will be fierce.
    if day_context['supply'] < (WATER_REQ * 1.2) and num_active_players > 1:
        current_bid = max(current_bid, DAILY_SALARY * 0.85) # Aggressive bid for scarce resource

    # Late game: Adjust strategy based on health and previous bids
    if remaining_days <= 2:
        if my_status['hp'] > 5: # Healthy late game
            if highest_prev_bid < DAILY_SALARY * 0.7: # If opponents were bidding low
                current_bid = min(current_bid, DAILY_SALARY * 0.65) # Try to save more
            else: # If opponents were competitive
                current_bid = min(current_bid, DAILY_SALARY * 0.85) # Don't overpay but stay competitive
        else: # Not healthy late game, bid high
            current_bid = max(current_bid, DAILY_SALARY * 0.95)
    # Early game: If rich, establish dominance but don't be reckless
    elif day_context['day'] <= 2 and my_status['budget'] > DAILY_SALARY * (EPISODE_DAYS / 2):
        current_bid = max(current_bid, DAILY_SALARY * 0.75)


    # --- 6. Final Bid Constraints ---
    # Cap the bid to a maximum reasonable value, slightly below full salary for strategic reasons
    max_strategic_bid = DAILY_SALARY * 0.96
    current_bid = min(current_bid, max_strategic_bid)

    # Ensure bid is always within budget and non-negative
    final_bid = min(my_status['budget'], max(0.0, current_bid))

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
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid: a fraction of daily salary. Start moderately.
    bid = DAILY_SALARY * 0.5

    # Adjust bid based on my current HP
    if my_status['hp'] <= 2: # Critical HP, must get water
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP
        bid = DAILY_SALARY * 0.8
    elif my_status['hp'] >= 8: # Good HP, can be more conservative
        bid = DAILY_SALARY * 0.4

    # Adjust bid based on supply scarcity
    # If supply is low, competition is likely higher.
    if day_context['supply'] <= WATER_REQ + 2: # Very scarce supply (e.g., 15-17 units)
        bid *= 1.2
    elif day_context['supply'] >= MAX_SUPPLY - 2: # Abundant supply (e.g., 23-25 units)
        bid *= 0.8

    # React to opponents' previous bids from 'previous_trace'
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            # If an opponent failed to get water and lost HP, they might bid higher today out of desperation.
            if prev.get('status') == 'NO_WATER' and prev.get('hp_after') is not None and prev['hp_after'] < opp['hp']:
                bid = max(bid, DAILY_SALARY * 0.75) # Consider bidding higher to secure water

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest previous bid was very high, competition is fierce.
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] <= 3: # Must get water
                bid = max(bid, highest_prev_bid * 1.05) # Bid slightly above to ensure win
            else: # Good HP, try to find a balance or slightly undercut if possible
                bid = max(bid, highest_prev_bid * 0.9) 
        # If highest previous bid was low, we can try to get water cheaper.
        elif highest_prev_bid <= DAILY_SALARY * 0.3:
            bid = min(bid, highest_prev_bid * 1.1) # Bid slightly above, but don't overpay
            bid = max(bid, DAILY_SALARY * 0.2) # Ensure a minimum reasonable bid
        else: # Moderate competition
            bid = max(bid, highest_prev_bid + 1.0) # Slightly exceed to win

    # Final adjustments
    # Ensure bid doesn't exceed current budget
    bid = min(my_status['budget'], bid)

    # Ensure bid is at least 1.0 to participate
    bid = max(1.0, bid)

    # If no opponents are alive, bid minimally to save budget
    if num_alive_opponents == 0:
        bid = min(my_status['budget'], DAILY_SALARY * 0.1)
        bid = max(1.0, bid) # Ensure it's at least 1.0

    return float(bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    episode_days = 10

    current_day = day_context['day']
    current_supply = day_context['supply']

    eric_last_bid = 0
    eric_alive = False
    if 'Eric' in opponents_status:
        eric_data = opponents_status['Eric']
        eric_alive = eric_data['alive']
        if eric_data.get('previous_trace'):
            eric_last_bid = eric_data['previous_trace'].get('bid', 0)

    bid_amount = DAILY_SALARY * 0.7

    if my_status['hp'] <= 2:
        bid_amount = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        bid_amount = DAILY_SALARY * 0.85

    if current_supply <= WATER_REQ:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.9)
    elif current_supply <= WATER_REQ * 2:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.75)

    if eric_alive and eric_last_bid > 0:
        bid_amount = max(bid_amount, eric_last_bid * 1.05)

    final_bid = min(my_status['budget'], bid_amount)

    final_bid = max(final_bid, 1.0)

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    EPISODE_DAYS = 10

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid - a flexible value that will be adjusted
    # Start with a moderate bid, slightly below daily salary
    target_bid = DAILY_SALARY * 0.75

    # 1. Adjust based on my HP and 'no_water_days' (desperation factor)
    if my_hp <= 2:
        target_bid = DAILY_SALARY * 1.2 # Very desperate
    elif my_hp <= 5:
        target_bid = DAILY_SALARY * 1.0 # Critical
    elif my_hp <= 8:
        target_bid = DAILY_SALARY * 0.85 # Moderate
    else:
        target_bid = DAILY_SALARY * 0.6 # Healthy, save money

    # Increase bid if I haven't received water recently
    if my_no_water_days > 0:
        target_bid *= (1 + my_no_water_days * 0.15) # Significant increase

    # 2. Adjust based on supply scarcity
    # Supply factor: 1.0 when supply is MIN_SUPPLY, 0.0 when supply is MAX_SUPPLY
    # This means higher multiplier for lower supply, indicating higher competition.
    supply_scarcity_factor = (MAX_SUPPLY - current_supply) / (MAX_SUPPLY - MIN_SUPPLY)
    target_bid *= (1 + supply_scarcity_factor * 0.2) # Up to 20% increase for very low supply

    # 3. Adjust based on opponents' previous bids (reactive strategy)
    highest_prev_bid_overall = 0.0
    highest_prev_bid_strong = 0.0 # From David or Eric

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid_value = prev['bid']
            highest_prev_bid_overall = max(highest_prev_bid_overall, bid_value)
            if opp['agent_id'] in ['David', 'Eric']:
                highest_prev_bid_strong = max(highest_prev_bid_strong, bid_value)

    if highest_prev_bid_strong > DAILY_SALARY * 0.8: # Strong opponents are bidding high
        if my_hp <= 8: # If not very healthy, try to outbid them
            target_bid = max(target_bid, highest_prev_bid_strong + 5)
        else: # If healthy, perhaps let them win and save budget, but still competitive
            target_bid = max(target_bid, highest_prev_bid_strong + 1)
    elif highest_prev_bid_overall > 0: # Some bidding occurred, but not necessarily high from strong players
        # If no strong high bids, or only weak opponents, bid slightly above the highest
        target_bid = max(target_bid, highest_prev_bid_overall + 1)

    # Ensure bid is at least a minimum to stay in the game, especially if healthy
    # This prevents bidding 0 or very low if all other factors push it down.
    if my_hp > 5: # If not desperate, ensure a reasonable minimum
        target_bid = max(target_bid, DAILY_SALARY * 0.3)
    else: # If desperate, ensure a higher minimum
        target_bid = max(target_bid, DAILY_SALARY * 0.7)

    # Final bid cannot exceed current budget
    final_bid = min(my_budget, target_bid)

    # Ensure bid is non-negative
    final_bid = max(0.0, final_bid)

    return round(final_bid, 2)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
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

    HIGH_BID_THRESHOLD = DAILY_SALARY * 0.85
    LOW_BID_CONSERVATIVE = DAILY_SALARY * 0.3
    HIGH_BID_DESPERATE = DAILY_SALARY * 0.95
    DEFAULT_STRONG_BID = DAILY_SALARY * 0.5
    CRITICAL_HP_BID = DAILY_SALARY * 0.9

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= HIGH_BID_THRESHOLD:
            if my_status['hp'] > 3:
                return min(my_status['budget'], LOW_BID_CONSERVATIVE)
            return min(my_status['budget'], HIGH_BID_DESPERATE)
        
        return min(my_status['budget'], max(DEFAULT_STRONG_BID, highest_prev_bid + 1.5))

    if my_status['hp'] <= 2:
        return min(my_status['budget'], CRITICAL_HP_BID)
    return min(my_status['budget'], DEFAULT_STRONG_BID)
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
    num_alive_opponents = len(alive_opponents)

    # Calculate available water slots. supply is float, result of // is float.
    available_water_slots = day_context['supply'] // WATER_REQ

    # 1. If no opponents, bid a small amount to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # 2. Critical HP: Bid very high
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # 3. Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_prev_bid = 0
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)

    # 4. Determine base bid
    base_bid = DAILY_SALARY * 0.55 # A moderate bid

    # Adjust bid based on competition and supply
    # If water is scarce relative to demand (including myself)
    if available_water_slots < num_alive_opponents + 1:
        # High competition: bid more aggressively
        if max_prev_bid > 0:
            base_bid = max(base_bid, max_prev_bid + 5) # Bid slightly above highest previous bid
        else:
            base_bid = DAILY_SALARY * 0.7 # No previous bids, but high competition

        # If it's late in the game, and I have budget, bid even higher
        days_remaining = EPISODE_DAYS - day_context['day']
        if days_remaining <= 3 and my_status['budget'] > DAILY_SALARY * 2: # Check if budget allows for aggressive late-game
            base_bid = max(base_bid, DAILY_SALARY * 0.85)

    else: # Sufficient water for everyone (less likely given supply range and WATER_REQ)
        if max_prev_bid > 0:
            # If previous bids were high, still need to compete
            if max_prev_bid >= DAILY_SALARY * 0.7:
                base_bid = max(base_bid, max_prev_bid + 1)
            else:
                base_bid = max(base_bid, max_prev_bid * 0.95) # Try to get it for slightly less if possible, but still competitive
        # If no previous bids, or they were low, stick to base_bid

    # Ensure bid doesn't exceed my budget or a reasonable maximum
    final_bid = min(my_status['budget'], base_bid)

    # Cap the bid to a reasonable max, e.g., 90% of daily salary, unless HP is critical
    if my_status['hp'] > 2:
        final_bid = min(final_bid, DAILY_SALARY * 0.9)

    # Ensure bid is at least 1 if I need water and have budget
    # my_status['hp'] starts at EPISODE_DAYS, so hp < EPISODE_DAYS means not full health
    if my_status['budget'] > 0 and my_status['hp'] < EPISODE_DAYS:
        final_bid = max(final_bid, 1)
    elif my_status['budget'] > 0 and my_status['hp'] == EPISODE_DAYS: # If full HP, bid low to save budget
        final_bid = min(final_bid, DAILY_SALARY * 0.2)

    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
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

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    else:
        highest_prev_bid = DAILY_SALARY * 0.5

    num_active_agents = len(alive_opponents) + 1
    total_water_demand = num_active_agents * WATER_REQ
    current_supply = day_context['supply']

    bid = 0.0
    if my_status['hp'] <= 2:
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5:
        bid = max(highest_prev_bid + 5, DAILY_SALARY * 0.8)
    else:
        if current_supply >= total_water_demand:
            bid = max(highest_prev_bid * 0.8, DAILY_SALARY * 0.4)
        else:
            bid = max(highest_prev_bid + 2, DAILY_SALARY * 0.6)

    return min(my_status['budget'], bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    # Calculate a base bid, which is already high due to fierce competition
    # Start with a high percentage of daily salary
    base_bid_percentage = 0.85 
    base_bid = DAILY_SALARY * base_bid_percentage

    # Adjust based on day progression - water becomes more critical later
    # Max increase of 15% over the course of the game
    day_progression_factor = (day_context['day'] / float(EPISODE_DAYS)) * 0.15 
    base_bid *= (1 + day_progression_factor)

    # High pressure / survival mode
    if my_status['hp'] <= 2: # Critical HP
        final_bid = DAILY_SALARY * 0.99
    elif my_status['hp'] <= 5 or my_status['no_water_days'] > 0: # Low HP or missed water
        final_bid = DAILY_SALARY * 0.95
    else:
        final_bid = base_bid

    # Analyze opponent's previous bids to stay competitive
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid low to save money
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    highest_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])

    # If opponents were bidding high, we must outbid them
    if highest_prev_bid > 0:
        # If highest previous bid was already very high, try to slightly exceed it
        if highest_prev_bid >= DAILY_SALARY * 0.9: # e.g., > 135
            final_bid = max(final_bid, highest_prev_bid + 1.0)
        # Otherwise, ensure we are competitive, potentially slightly above the highest
        else:
            final_bid = max(final_bid, highest_prev_bid + 0.5)
            
    # Ensure a minimum competitive bid even without strong prior signals
    final_bid = max(final_bid, DAILY_SALARY * 0.8)

    # Ensure bid does not exceed budget and is positive
    final_bid = min(final_bid, my_status['budget'])
    final_bid = max(1.0, final_bid) # Bid at least 1.0

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid = DAILY_SALARY * 0.65

    if my_hp <= 2 or my_no_water_days > 0:
        bid = DAILY_SALARY * 0.95
    elif my_hp <= 4:
        bid = DAILY_SALARY * 0.8

    if current_day >= EPISODE_DAYS - 2:
        bid = max(bid, DAILY_SALARY * 0.9)
    elif current_day >= EPISODE_DAYS / 2:
        bid = max(bid, DAILY_SALARY * 0.7)

    num_competitors = len(alive_opponents) + 1
    max_water_units = int(current_supply // WATER_REQ)

    if max_water_units < num_competitors:
        if my_hp > 4:
            bid = max(bid, DAILY_SALARY * 0.75)
        else:
            bid = max(bid, DAILY_SALARY * 0.9)
    elif max_water_units >= num_competitors * 2 and my_hp > 5:
        bid = min(bid, DAILY_SALARY * 0.55)

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        
        if max_yesterday_bid >= DAILY_SALARY * 0.7:
            if my_hp <= 4:
                bid = max(bid, max_yesterday_bid + 5)
            elif my_hp > 4 and max_water_units < num_competitors * 1.5:
                 bid = max(bid, max_yesterday_bid + 1)
        elif max_yesterday_bid < DAILY_SALARY * 0.5 and my_hp > 5 and max_water_units >= num_competitors:
            bid = min(bid, max_yesterday_bid + 10)

    final_bid = max(1.0, min(my_budget, bid))

    return final_bid
"""
