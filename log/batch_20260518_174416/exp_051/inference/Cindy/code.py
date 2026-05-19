# ============================================================
# Experiment: exp_051
# Agent: Cindy
# Source: exp_051
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    total_known_demand = WATER_REQ
    for opp in alive_opponents:
        total_known_demand += opp['water_requirement']

    bid = DAILY_SALARY * 0.5

    if supply < total_known_demand:
        shortfall_ratio = total_known_demand / supply
        if shortfall_ratio >= 2:
            bid = DAILY_SALARY * 0.95
        elif shortfall_ratio >= 1.5:
            bid = DAILY_SALARY * 0.8
        else:
            bid = DAILY_SALARY * 0.7
    else:
        surplus_ratio = supply / total_known_demand
        if surplus_ratio >= 2:
            bid = DAILY_SALARY * 0.3
        elif surplus_ratio >= 1.5:
            bid = DAILY_SALARY * 0.4
        else:
            bid = DAILY_SALARY * 0.5

    if my_status['hp'] <= 2:
        bid = max(bid, DAILY_SALARY * 0.9)
    elif my_status['hp'] <= 4:
        bid = max(bid, DAILY_SALARY * 0.75)

    return min(my_status['budget'], bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_HP = 10
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Emergency: Low HP, bid aggressively for survival
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # End game: Last days, ensure survival
    if day_context['day'] >= EPISODE_DAYS - 1: 
        return min(my_status['budget'], DAILY_SALARY * 0.9)

    # No opponents: Bid minimal to conserve budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and prev.get('status') != 'error':
            yesterday_bids.append(prev['bid'])

    # Calculate base bid
    base_bid = DAILY_SALARY * 0.5
    bid = base_bid

    # Adjust bid based on current supply vs. estimated demand
    estimated_total_demand = WATER_REQ * (num_alive_opponents + 1)
    # Avoid division by zero if for some reason estimated_total_demand is 0 (should not happen with WATER_REQ > 0)
    supply_ratio = day_context['supply'] / estimated_total_demand if estimated_total_demand > 0 else 1.0

    if supply_ratio < 0.8: # Supply is tight
        bid = max(bid, DAILY_SALARY * 0.6) # Increase baseline for tight supply
        if yesterday_bids:
            bid = max(bid, max(yesterday_bids) * 1.1) # Bid aggressively above highest
    elif supply_ratio > 1.2: # Supply is abundant
        bid = min(bid, DAILY_SALARY * 0.4) # Decrease baseline for abundant supply
        if yesterday_bids:
            bid = min(bid, (sum(yesterday_bids) / len(yesterday_bids)) * 0.9) # Try to bid slightly below average
    else: # Moderate supply
        if yesterday_bids:
            bid = max(bid, (sum(yesterday_bids) / len(yesterday_bids)) * 1.05) # Slightly above average

    # Add a small buffer if HP is not full, reflecting increased urgency
    if my_status['hp'] < MAX_HP:
        hp_penalty = (MAX_HP - my_status['hp']) / MAX_HP # 0 to 1
        bid += DAILY_SALARY * 0.1 * hp_penalty # Max 10% of salary for very low HP

    # Ensure bid doesn't exceed budget and is at least 1 (if budget allows)
    final_bid = min(my_status['budget'], bid)
    if my_status['budget'] > 0:
        final_bid = max(1.0, final_bid)
    else:
        final_bid = 0.0 # Cannot bid if no budget

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid: a moderate value, adjusted by HP and supply
    base_bid = DAILY_SALARY * 0.5

    # Adjust base bid based on my HP
    if my_status['hp'] <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.7
    elif my_status['hp'] >= 7: # Healthy HP
        base_bid = DAILY_SALARY * 0.4

    # Adjust based on current supply
    current_supply = day_context['supply']
    if current_supply <= WATER_REQ * 1.5: # Supply is tight
        base_bid *= 1.1
    elif current_supply >= MAX_SUPPLY - 2: # Supply is abundant
        base_bid *= 0.9

    # Adjust based on day (late game pressure)
    days_left = EPISODE_DAYS - day_context['day']
    if days_left <= 3 and my_status['hp'] <= 5: # Late game, low HP
        base_bid = max(base_bid, DAILY_SALARY * 0.85)
    elif days_left <= 1 and my_status['hp'] <= 3: # Very late game, critical HP
        base_bid = max(base_bid, DAILY_SALARY * 0.98)

    # Opponent reaction logic
    if num_alive_opponents == 0:
        # No opponents, bid minimally
        return min(my_status['budget'], 10.0) # Bid a small amount to get water

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents bid high yesterday, I need to be more aggressive
        if highest_prev_bid >= DAILY_SALARY * 0.7:
            # If my HP is good, I can try to outbid by a small margin or stick to my calculated bid if it's already high enough
            if my_status['hp'] > 4:
                base_bid = max(base_bid, highest_prev_bid + 2)
            else: # If low HP, I must fight for water
                base_bid = max(base_bid, highest_prev_bid + 5)
        # If opponents bid moderately or low, I can try to secure water efficiently
        elif highest_prev_bid > 0: # Any bid indicates competition
            # If my HP is good, try to win cheaply but surely
            if my_status['hp'] > 5:
                base_bid = min(base_bid, highest_prev_bid + 10) # Bid slightly above but not excessively
            else: # If HP is not great, ensure I get water
                base_bid = max(base_bid, highest_prev_bid + 3)

    # Ensure bid is at least 1.0 and within budget
    final_bid = max(1.0, base_bid)
    return min(my_status['budget'], final_bid)
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

    if not alive_opponents:
        return max(0.01, min(my_status['budget'], DAILY_SALARY * 0.2))

    if my_status['hp'] <= 2:
        return max(0.01, min(my_status['budget'], DAILY_SALARY * 0.98))
    if my_status['no_water_days'] > 0:
        return max(0.01, min(my_status['budget'], DAILY_SALARY * 0.9))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_bid = DAILY_SALARY * 0.6

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 5:
                current_bid = max(current_bid, highest_prev_bid * 1.05)
            else:
                current_bid = max(current_bid, highest_prev_bid + 10)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            current_bid = max(current_bid, highest_prev_bid + 5)
        else:
            current_bid = max(current_bid, highest_prev_bid + 15)
    
    supply_units = day_context['supply'] / WATER_REQ
    
    if supply_units < 2:
        current_bid *= 1.15
    elif day_context['supply'] < (num_alive_opponents + 1) * WATER_REQ:
        current_bid *= 1.25
    elif supply_units > num_alive_opponents + 2:
        current_bid *= 0.9
    
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2:
        if my_status['hp'] < 5:
            current_bid = max(current_bid, DAILY_SALARY * 0.9)
        else:
            current_bid = max(current_bid, DAILY_SALARY * 0.5)
    
    current_bid = max(current_bid, DAILY_SALARY * 0.3)

    final_bid = min(my_status['budget'], current_bid)
    return max(0.01, final_bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_players = len(alive_opponents) + 1 # Including myself

    # Calculate how many water units are available for players
    available_water_units = int(current_supply / WATER_REQ)

    # Base bid: Default to a reasonable fraction of salary
    bid = DAILY_SALARY * 0.5

    # Survival logic: If HP is low, bid aggressively
    if my_hp <= 2: # Critical health
        bid = DAILY_SALARY * 0.9
    elif my_hp <= 4: # Low health
        bid = DAILY_SALARY * 0.75

    # React to opponent's yesterday bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)

        # Adjust bid based on max previous bid and supply/demand
        if available_water_units < num_alive_players: # Supply is tight, higher competition
            if my_hp <= 2: # Critical, must win
                bid = max(bid, max_prev_bid + 5) # Bid slightly above max
            elif my_hp <= 4: # Low health, try to win
                bid = max(bid, max_prev_bid + 2) # Bid above max if not too high
            else: # Healthy, but supply is tight, be competitive
                bid = max(bid, max_prev_bid * 1.02) # Slightly above max
        else: # Supply is abundant, can be more conservative
            if my_hp <= 2: # Still critical, but maybe don't need to overbid
                bid = max(bid, max_prev_bid * 1.1)
            elif my_hp <= 4:
                bid = max(bid, max_prev_bid * 1.0)
            else: # Healthy, can try to save money
                bid = min(bid, max_prev_bid * 0.95) # Try to get it cheaper, but don't go too low

    # End game strategy: If few days left, be more aggressive to survive
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_hp > 0: # Last 2 days
        bid = max(bid, DAILY_SALARY * 0.85) # Ensure high bid to survive

    # Ensure bid doesn't exceed budget or is negative
    bid = min(bid, my_budget)
    bid = max(bid, 0.01) # Minimum bid to participate

    # Cap bid at a reasonable maximum
    if my_hp > 2:
        bid = min(bid, DAILY_SALARY * 1.2) # Don't overspend too much if healthy
    else: # Critical HP, allow higher bids if needed
         bid = min(bid, DAILY_SALARY * 1.5) # Allow bidding up to 1.5x salary if critical

    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    TOTAL_DAYS = 10 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimal to save budget, since supply (15-25) is always enough for my 13.
    if not alive_opponents:
        return 1.0

    # Calculate total water needed by all alive players (including myself)
    total_water_needed_by_alive = WATER_REQ
    for opp in alive_opponents:
        total_water_needed_by_alive += opp['water_requirement']

    is_competitive_day = day_context['supply'] < total_water_needed_by_alive

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid
    bid = 0.0

    # Desperate state (low HP) - bid very aggressively
    if my_status['hp'] <= 2:
        bid = DAILY_SALARY * 0.95
    # Medium HP - try to be strategic
    elif my_status['hp'] <= 4: # More aggressive if HP is getting low, but not desperate
        if is_competitive_day:
            if yesterday_bids:
                highest_prev_bid = max(yesterday_bids)
                bid = max(highest_prev_bid + 10, DAILY_SALARY * 0.85) # Ensure water
            else:
                bid = DAILY_SALARY * 0.8 # Aggressive on first competitive day
        else: # Not competitive, but HP is medium
            if yesterday_bids:
                avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)
                bid = max(avg_prev_bid * 1.1, DAILY_SALARY * 0.6) # Slightly above avg to be safe
            else:
                bid = DAILY_SALARY * 0.55 # Moderate on first non-competitive day
    # Healthy HP - more flexible
    else: # my_status['hp'] > 4
        if is_competitive_day:
            if yesterday_bids:
                highest_prev_bid = max(yesterday_bids)
                # Bid just above highest or a solid amount if competitive
                bid = max(highest_prev_bid + 5, DAILY_SALARY * 0.75)
            else:
                bid = DAILY_SALARY * 0.7 # Solid bid for first competitive day
        else: # Not competitive day
            if yesterday_bids:
                avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)
                # Try to save money, bid below average or a safe low amount
                bid = max(avg_prev_bid * 0.8, DAILY_SALARY * 0.3)
            else:
                bid = DAILY_SALARY * 0.25 # Very low on first non-competitive day

    # Ensure bid does not exceed current budget
    bid = min(bid, my_status['budget'])
    
    # Consider remaining days and budget to prevent overspending too early
    current_day = day_context['day']
    days_left_including_today = TOTAL_DAYS - current_day + 1
    if days_left_including_today > 0:
        avg_budget_per_day = my_status['budget'] / days_left_including_today
        # If current bid is too high for remaining budget, try to reduce it
        # But only if HP is good. If HP is low, survival is priority.
        if bid > avg_budget_per_day + (DAILY_SALARY * 0.1) and my_status['hp'] > 2:
            bid = min(bid, avg_budget_per_day + (DAILY_SALARY * 0.1))

    # Ensure a minimum bid to participate
    bid = max(1.0, bid)

    return bid
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
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], 1.0)

    base_bid = DAILY_SALARY * 0.6

    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.85
    elif my_status['hp'] <= 6 and (EPISODE_DAYS - day_context['day'] + 1) <= 3:
        base_bid = DAILY_SALARY * 0.8

    if day_context['supply'] <= WATER_REQ + 2:
        base_bid *= 1.1
            
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    final_bid = base_bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 5:
                final_bid = max(final_bid, highest_prev_bid + 2.0)
            else:
                final_bid = max(final_bid, highest_prev_bid + 5.0, DAILY_SALARY * 0.98)
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            final_bid = max(final_bid, highest_prev_bid + 1.5)
        else:
            final_bid = max(final_bid, highest_prev_bid + 1.0)
    
    final_bid = max(0.1, final_bid)
    final_bid = min(my_status['budget'], final_bid)

    if my_status['hp'] <= 3 and my_status['budget'] < DAILY_SALARY * 0.7:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.9)

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    day = day_context['day']
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    # --- Survival Logic ---
    # If HP is critically low or I haven't received water recently, bid very aggressively.
    if my_hp <= 2 or my_no_water_days >= 1:
        return min(my_budget, DAILY_SALARY * 0.95)
    # If HP is low, bid aggressively.
    if my_hp <= 4:
        return min(my_budget, DAILY_SALARY * 0.85)

    # --- Opponent Analysis based on previous_trace ---
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    num_alive_opponents = len(alive_opponents)

    # --- Bidding Logic based on competition and supply ---

    # If no opponents or no previous bids (e.g., first day or all opponents died/didn't bid)
    if not yesterday_bids:
        # Base bid: a fraction of daily salary. Adjust based on supply.
        base_bid = DAILY_SALARY * 0.6
        if supply >= MAX_SUPPLY * 0.8: # High supply, less competition
            base_bid = DAILY_SALARY * 0.45
        elif supply <= MIN_SUPPLY * 1.2: # Low supply, more competition
            base_bid = DAILY_SALARY * 0.7
        
        # Consider remaining days and budget. Don't overspend too early if budget is tight.
        remaining_days = EPISODE_DAYS - day + 1
        if remaining_days > 0 and my_budget / remaining_days < DAILY_SALARY * 0.5:
            base_bid = min(base_bid, DAILY_SALARY * 0.4)
            if my_hp <= 6: # Still need water, but be careful
                base_bid = max(base_bid, DAILY_SALARY * 0.6)

        return min(my_budget, base_bid)

    # If there are previous bids, react to them
    highest_prev_bid = max(yesterday_bids)
    average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

    # Check for very high opponent pressure
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if my_hp > 6: # Good HP, can afford to be less aggressive to save budget
            return min(my_budget, DAILY_SALARY * 0.4) # Try to save, let them overspend
        else: # HP is not good enough, must compete
            return min(my_budget, highest_prev_bid + 5) # Bid slightly higher to win

    # Check for very low opponent pressure
    if highest_prev_bid <= DAILY_SALARY * 0.3:
        # Bid slightly above the highest to win cheaply, but ensure a minimum
        return min(my_budget, max(highest_prev_bid + 2, DAILY_SALARY * 0.25))

    # Moderate pressure: bid slightly above average or highest, adjusted for supply and day
    target_bid = average_prev_bid * 1.05 # Slightly above average
    
    # Adjust based on supply
    if supply >= MAX_SUPPLY * 0.8: # High supply
        target_bid = max(target_bid * 0.9, DAILY_SALARY * 0.4)
    elif supply <= MIN_SUPPLY * 1.2: # Low supply
        target_bid = min(target_bid * 1.1, DAILY_SALARY * 0.8)

    # Adjust for number of opponents (more opponents -> more competition -> higher bid)
    target_bid += num_alive_opponents * 1.5 # Small increment per opponent

    # Ensure bid is reasonable and within budget
    bid = min(my_budget, max(target_bid, DAILY_SALARY * 0.5)) # Ensure a minimum bid of 50% salary if not critical

    # Final sanity check for bid value
    return max(1.0, bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no active opponents, bid low to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Base bid is aggressive due to high competition for water (only one can get full 13 units)
    base_bid = DAILY_SALARY * 0.85 # Default aggressive bid

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were bidding high, we need to match or slightly exceed
        if highest_prev_bid >= DAILY_SALARY * 0.9: # If highest bid was 90% of salary or more
            base_bid = max(base_bid, highest_prev_bid + 2.0) # Try to outbid by a small margin
        elif highest_prev_bid > DAILY_SALARY * 0.7: # If bid was moderately high
            base_bid = max(base_bid, highest_prev_bid + 1.0)
            
    # Adjust bid further based on my current HP
    if my_status['hp'] <= 2: # Critical HP, must win
        final_bid = DAILY_SALARY * 1.05 # Bid significantly above salary
    elif my_status['hp'] <= 4: # Low HP
        final_bid = max(base_bid, DAILY_SALARY * 1.0) # Ensure at least salary
    elif my_status['hp'] <= 6: # Medium-low HP
        final_bid = max(base_bid, DAILY_SALARY * 0.95)
    else: # Healthy HP
        final_bid = max(base_bid, DAILY_SALARY * 0.9) # Still aggressive due to competition

    # Cap the bid by current budget
    final_bid = min(my_status['budget'], final_bid)
    
    # Ensure bid is never zero or negative
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

    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # 1. If no opponents, bid minimal to save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.05)

    # 2. Survival Mode: If HP is very low or no water for 1 day, bid very high
    #    Also consider late game desperation
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        # If it's a very late day and I'm low on HP, go almost all in
        if current_day >= EPISODE_DAYS - 2 and my_status['hp'] <= 3:
            return min(my_status['budget'], DAILY_SALARY * 0.99)
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # 3. Analyze opponents' previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # 4. Determine competitive bid (water is always scarce for multiple players given supply range)
    base_competitive_bid = DAILY_SALARY * 0.6 
    my_calculated_bid = base_competitive_bid # Default competitive bid

    if highest_prev_bid > 0:
        # If highest_prev_bid is very high, I need to beat it significantly to guarantee win
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            my_calculated_bid = highest_prev_bid + 10.0
        # If highest_prev_bid is moderate, beat it by a smaller margin
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            my_calculated_bid = highest_prev_bid + 5.0
        # If highest_prev_bid is low, ensure I win it
        else:
            my_calculated_bid = max(base_competitive_bid, highest_prev_bid + 2.0)
    
    # Further adjust if my HP is getting low (but not critical survival mode yet)
    if my_status['hp'] <= 5:
        my_calculated_bid = max(my_calculated_bid, DAILY_SALARY * 0.75) # Be more aggressive
    elif my_status['hp'] > 5: # Healthy, can be slightly less aggressive if not needed
        my_calculated_bid = max(my_calculated_bid, DAILY_SALARY * 0.5)

    # 5. Budget Constraint & Minimum Bid
    final_bid = min(my_status['budget'], my_calculated_bid)

    # Ensure bid is at least 1.0 if I have budget and need water
    if my_status['hp'] <= 8 and my_status['budget'] > 0 and final_bid < 1.0:
        final_bid = 1.0

    return max(1.0, final_bid)
"""
