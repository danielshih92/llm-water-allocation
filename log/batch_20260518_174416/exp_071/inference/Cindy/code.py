# ============================================================
# Experiment: exp_071
# Agent: Cindy
# Source: exp_071
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

    current_supply = day_context['supply']

    # If no opponents, bid minimally to get water
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.05) # Bid very low

    # --- Determine base bid based on my HP ---
    if my_status['hp'] <= 2:  # Critical HP, need water desperately
        bid_amount = DAILY_SALARY * 0.95
    elif my_status['hp'] == 3: # Low HP
        bid_amount = DAILY_SALARY * 0.75
    elif my_status['hp'] <= 5: # Moderate HP
        bid_amount = DAILY_SALARY * 0.55
    else: # Comfortable HP
        bid_amount = DAILY_SALARY * 0.4

    # --- Adjust bid based on supply and competition ---
    estimated_total_demand = (num_alive_opponents + 1) * WATER_REQ

    # Avoid division by zero if estimated_total_demand is 0 (shouldn't happen with +1)
    scarcity_ratio = current_supply / estimated_total_demand if estimated_total_demand > 0 else 1.0

    if scarcity_ratio < 0.7: # Very scarce supply
        # Be more aggressive, especially if not at very high HP
        if my_status['hp'] <= 5:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.8)
        else: # If HP is high, still be competitive but don't overbid
            bid_amount = max(bid_amount, DAILY_SALARY * 0.6)
    elif scarcity_ratio > 1.5: # Abundant supply
        # Be less aggressive if HP is comfortable
        if my_status['hp'] > 3:
            bid_amount = min(bid_amount, DAILY_SALARY * 0.3)

    # --- React to yesterday's highest bid (if available) ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were bidding very high, we need to counter
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] <= 3: # Critical/Low HP, must get water
                bid_amount = max(bid_amount, highest_prev_bid + 5)
            else: # Comfortable HP, try to win but don't overspend too much
                bid_amount = max(bid_amount, highest_prev_bid * 0.95) # Slightly less than highest to see if we can get cheaper
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderate competition
            if my_status['hp'] <= 4:
                bid_amount = max(bid_amount, highest_prev_bid + 2)
            else:
                bid_amount = min(bid_amount, highest_prev_bid * 0.8) # Try to underbid if comfortable
        else: # Low competition yesterday
            if my_status['hp'] > 4:
                bid_amount = min(bid_amount, highest_prev_bid * 0.75) # Conserve more
            # If HP is low, maintain base bid

    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], bid_amount)

    # Ensure a minimal bid if budget allows and calculated bid is very low
    if final_bid < 1 and my_status['budget'] > 0:
        return 1.0 # Bid at least 1 if possible
    elif my_status['budget'] == 0:
        return 0.0 # No budget, no bid

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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # 1. Emergency Bid: If HP is very low or no water for days
    if my_hp <= 2 or my_no_water_days >= 1:
        return min(my_budget, DAILY_SALARY * 0.95)

    # 2. Last Day Bid: If it's the final day and I still need to survive
    if current_day == EPISODE_DAYS and my_hp > 0:
        return min(my_budget, DAILY_SALARY * 0.99)

    # 3. No Opponents: If no active competition
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.3) # Bid low

    # Get yesterday's highest bid from all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Given that supply is always tight (max 25, my_req 13, so only 1 full slot),
    # competition for the full 13 units will always be high if more than one agent is alive.
    
    bid_value = 0.0

    # If yesterday's highest bid was already significant
    if highest_prev_bid >= DAILY_SALARY * 0.7:
        # Bid slightly above to win, but with a cap
        bid_value = max(DAILY_SALARY * 0.6, highest_prev_bid * 1.05)
        bid_value = min(bid_value, DAILY_SALARY * 0.85) # Cap to avoid overspending too much
    else:
        # If yesterday's highest bid was not super high, but water is still competitive
        # Bid a solid amount to secure water, as supply is always tight for multiple full requirements.
        bid_value = DAILY_SALARY * 0.65

    # Ensure bid does not exceed budget
    final_bid = min(my_budget, bid_value)

    # Ensure bid is at least 1 if I need water and have budget, and not in a death spiral
    if my_hp > 0 and final_bid <= 0 and my_budget > 0:
        final_bid = min(my_budget, 1.0)

    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    base_bid = DAILY_SALARY * 0.5

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    my_bid = base_bid

    if my_status['hp'] <= 2:
        # Critical HP, bid very high to survive
        my_bid = DAILY_SALARY * 0.95 
    elif my_status['hp'] <= 4:
        # Low HP, bid high, try to beat yesterday's max or a high baseline
        if highest_prev_bid > 0:
            my_bid = max(highest_prev_bid + 5, DAILY_SALARY * 0.8)
        else:
            my_bid = DAILY_SALARY * 0.85
    else: 
        # Healthy HP
        if highest_prev_bid > DAILY_SALARY * 0.7:
            # Opponents are bidding high, slightly outbid them
            my_bid = highest_prev_bid + 2 
        elif highest_prev_bid > 0:
            # Opponents are bidding moderately, slightly outbid them
            my_bid = highest_prev_bid + 1 
        else:
            # No clear history or low bids, bid moderately
            my_bid = DAILY_SALARY * 0.6 

    # Adjust for supply: if supply is tight, increase bid slightly
    num_alive_opponents = len(alive_opponents)
    if day_context['supply'] <= WATER_REQ + 5 and num_alive_opponents >= 1: # Supply 15-18
        my_bid *= 1.1 # Increase bid by 10%

    # Ensure bid does not exceed current budget
    my_bid = min(my_status['budget'], my_bid)
    # Ensure bid is at least a minimum positive amount
    my_bid = max(my_bid, 1.0)

    return my_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Calculate a base bid
    # This bid aims to secure water without overspending
    base_bid = DAILY_SALARY * 0.6

    # Adjust base bid based on current supply and number of competitors
    # If supply is low, competition is high, bid more aggressively
    # If supply is high, competition is lower, can bid less
    # Supply range [15, 25]
    supply_pressure_factor = 1 - ((current_supply - 15) / (25 - 15)) # 1.0 for supply=15, 0.0 for supply=25
    base_bid += (DAILY_SALARY * 0.4) * supply_pressure_factor # Add up to 40% of salary based on supply pressure

    # Adjust bid based on my HP (no_water_days)
    # If HP is low, bid very aggressively
    if my_hp <= 2: # Critical HP
        base_bid = max(base_bid, DAILY_SALARY * 0.9) # Must get water
    elif my_hp <= 4: # Low HP
        base_bid = max(base_bid, DAILY_SALARY * 0.75)
    
    # Get opponents' previous bids
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
    
    # If there were previous bids, adjust based on highest
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest bid was very high, we might need to match or slightly exceed
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Aggressive opponent
            if my_hp <= 3: # If my HP is low, I must compete
                base_bid = max(base_bid, highest_prev_bid + 5) # Bid slightly above
            else: # If my HP is good, I can decide to conserve or compete
                base_bid = max(base_bid, highest_prev_bid * 0.95) # Try to get it for slightly less
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderate opponent
            base_bid = max(base_bid, highest_prev_bid + 1) # Bid slightly above
        # If highest bid was low, our base_bid might already be higher, which is fine.
    
    # Consider end-game aggressiveness
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last few days, need to survive
        if my_hp <= 5: # If HP is not great, be very aggressive
            base_bid = max(base_bid, DAILY_SALARY * 0.95)
        else: # If HP is good, maintain a strong bid
            base_bid = max(base_bid, DAILY_SALARY * 0.7)

    # Ensure bid does not exceed budget
    final_bid = min(my_budget, base_bid)

    # Ensure bid is at least a minimal amount to indicate participation if budget allows
    if final_bid == 0 and my_budget > 0:
        final_bid = min(my_budget, 1.0) # Bid 1 if budget allows and calculated bid is 0

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid very low to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    eric_is_alive = False
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            if opp_id == "Eric":
                eric_is_alive = True
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

    # Default bid if no previous bids or specific conditions met
    bid_amount = DAILY_SALARY * 0.55 # Base moderate bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if eric_is_alive:
            # Eric is a strong opponent, needs aggressive countering
            if highest_prev_bid >= DAILY_SALARY * 0.85: # 127.5
                if my_status['hp'] > 4: # Good HP, but still need to compete strongly
                    bid_amount = max(DAILY_SALARY * 0.8, highest_prev_bid + 5) # 120 or higher
                else: # Low HP, must win
                    bid_amount = DAILY_SALARY * 0.99 # 148.5
            else: # Eric's previous bid was not extremely high, but still be competitive
                bid_amount = max(DAILY_SALARY * 0.65, highest_prev_bid + 2.5) # 97.5 or higher
        else:
            # Eric is not alive, other opponents are less of a threat
            if highest_prev_bid >= DAILY_SALARY * 0.85: # 127.5
                if my_status['hp'] > 3:
                    # If HP is good and others are overbidding, save budget
                    bid_amount = DAILY_SALARY * 0.3 # 45
                else:
                    # Low HP, need water
                    bid_amount = DAILY_SALARY * 0.95 # 142.5
            else:
                # Moderate bids from others, react accordingly
                bid_amount = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5) # 75 or higher
    
    # Override for critically low HP, regardless of opponent bids
    if my_status['hp'] <= 2:
        bid_amount = DAILY_SALARY * 0.99 # 148.5

    # Ensure bid doesn't exceed budget
    final_bid = min(my_status['budget'], bid_amount)

    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Scenario 1: No active opponents
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1) # Bid low to save budget

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Scenario 2: Critical HP - Must get water
    if my_hp <= 3:
        return min(my_budget, DAILY_SALARY * 0.95) # Bid very aggressively

    # Scenario 3: Low HP - Need water soon
    if my_hp <= 5:
        return min(my_budget, DAILY_SALARY * 0.8) # Bid aggressively

    # Scenario 4: Normal HP - React to opponent's yesterday bids and supply
    base_bid = DAILY_SALARY * 0.6 # Default moderate-aggressive bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were very aggressive yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, highest_prev_bid + 5.0) # Try to outbid significantly
        # If opponents were moderately aggressive or low
        else:
            base_bid = max(base_bid, highest_prev_bid + 2.0) # Slightly outbid

    # Adjust for supply scarcity if not already covered by HP or high previous bids
    # If supply is only enough for one person (or barely two for WATER_REQ=13)
    if current_supply < WATER_REQ * 1.5 and my_hp > 5: # Supply is tight, but not critical HP
        base_bid = max(base_bid, DAILY_SALARY * 0.75) # Ensure a good bid

    # Ensure the bid does not exceed current budget
    final_bid = min(my_budget, base_bid)

    # Final check for minimal bid if I need water but current logic resulted in a very low bid
    if my_hp < 10 and my_budget > 0 and final_bid < DAILY_SALARY * 0.2:
        final_bid = min(my_budget, DAILY_SALARY * 0.2) # Bid at least 20% of salary if needing water

    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # Hardcoded from meta-round state

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid
    bid = DAILY_SALARY * 0.5 # Default moderate bid

    # Adjust bid based on my desperation
    if my_no_water_days > 0:
        bid = DAILY_SALARY * 0.9
        if my_no_water_days >= 2: # More desperate
            bid = DAILY_SALARY * 1.1
    elif my_current_hp <= 2: # Critical HP
        bid = DAILY_SALARY * 1.0
    elif my_current_hp <= 4: # Low HP
        bid = DAILY_SALARY * 0.75

    # Analyze opponent's yesterday behavior
    yesterday_bids = []
    opponents_desperate_yesterday = 0
    opponents_low_hp_yesterday = 0

    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                yesterday_bids.append(prev_trace['bid'])
                if prev_trace.get('no_water_days', 0) > 0:
                    opponents_desperate_yesterday += 1
                if prev_trace.get('hp_after', 100) <= 2: # Assume high initial HP, 100 is a safe default
                    opponents_low_hp_yesterday += 1

    # Adjust bid based on opponent pressure
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        if max_prev_bid > DAILY_SALARY * 0.8: # High competition pressure
            bid = max(bid, max_prev_bid + 5)
        elif avg_prev_bid > DAILY_SALARY * 0.6: # Moderate competition
            bid = max(bid, avg_prev_bid + 2)
        else: # Low competition, try to get water cheaper
            bid = max(bid, avg_prev_bid * 1.1)

    # Adjust bid based on supply scarcity
    total_water_needed = (num_alive_opponents + 1) * WATER_REQ # Including myself
    if current_supply < total_water_needed:
        # High scarcity, increase bid significantly
        bid += (total_water_needed - current_supply) * (DAILY_SALARY / WATER_REQ / 2) # Scale increase
    elif current_supply < (num_alive_opponents + 1) * WATER_REQ * 1.2: # Moderate scarcity
        bid += 10 # Small increase

    # Adjust bid for end-game desperation
    days_remaining = EPISODE_DAYS - current_day
    if days_remaining <= 2: # Last two days
        bid = max(bid, DAILY_SALARY * 1.2) # Bid very aggressively
    elif days_remaining <= 4: # Approaching end
        bid = max(bid, DAILY_SALARY * 0.9)

    # Consider opponents who were desperate yesterday
    if opponents_desperate_yesterday > 0:
        bid += opponents_desperate_yesterday * 8 # Slightly increase bid per desperate opponent

    # Final budget constraint and non-negative bid
    final_bid = min(my_current_budget, bid)
    final_bid = max(0.0, final_bid) # Bid cannot be negative

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid: Start with a competitive bid, slightly below daily salary
    target_bid = DAILY_SALARY * 0.75 # 112.5

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Adjust target_bid based on yesterday's highest bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were bidding high, I need to raise my bid to stay competitive.
        # Add a small buffer to try and win.
        target_bid = max(target_bid, highest_prev_bid + 5.0)
    
    # Adjust target_bid based on my HP (survival priority)
    if my_status['hp'] <= 1: # Critical - 1 day left before death
        target_bid = DAILY_SALARY * 0.99 # Bid almost everything to survive
    elif my_status['hp'] <= 3: # Very low HP - 2 days left before death
        target_bid = max(target_bid, DAILY_SALARY * 0.95) # High bid
    elif my_status['hp'] <= 5: # Low HP - 3-4 days left
        target_bid = max(target_bid, DAILY_SALARY * 0.85) # Aggressive bid
    elif my_status['hp'] >= 8: # Healthy HP - can afford to be slightly less aggressive if budget is tight
        target_bid = max(target_bid, DAILY_SALARY * 0.65) # Still competitive, but not desperate
    
    # Consider current day and remaining days for long-term budget management
    current_day = day_context['day']
    remaining_days = EPISODE_DAYS - current_day

    # If it's the last few days
    if remaining_days <= 2:
        if my_status['hp'] > remaining_days: # Can survive without water for the remaining days
            # Try to win, but don't overspend if not critical
            target_bid = max(target_bid, DAILY_SALARY * 0.7)
        else: # Must get water to survive
            target_bid = max(target_bid, DAILY_SALARY * 0.98) # Very aggressive

    # Final bid cannot exceed current budget
    final_bid = min(my_status['budget'], target_bid)

    # Ensure a minimum bid if budget allows, to avoid being ignored or underbidding by too much
    if final_bid < DAILY_SALARY * 0.1 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.1)
    elif my_status['budget'] == 0: # If no budget, bid 0
        final_bid = 0.0

    return float(final_bid)
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
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    bid_amount = DAILY_SALARY * 0.6

    if my_status['hp'] <= 2:
        bid_amount = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5:
        bid_amount = DAILY_SALARY * 0.8
    else:
        bid_amount = DAILY_SALARY * 0.5

    if highest_prev_bid > 0:
        if my_status['hp'] <= 5:
            bid_amount = max(bid_amount, highest_prev_bid + 5)
        else:
            bid_amount = max(bid_amount, highest_prev_bid * 0.9)

    supply = day_context['supply']
    if supply <= 18:
        bid_amount *= 1.05
    elif supply >= 22:
        bid_amount *= 0.95

    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] <= 5:
        bid_amount = DAILY_SALARY * 0.99

    final_bid = min(my_status['budget'], bid_amount)

    return max(1.0, final_bid)
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
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    days_left = EPISODE_DAYS - current_day + 1

    # --- Emergency Bidding for Low HP ---
    if my_hp <= 2: # Critical health, almost dying
        return min(my_budget, DAILY_SALARY * 0.95)
    elif my_hp <= 4 and my_no_water_days > 0: # Low HP and already missed water yesterday
        return min(my_budget, DAILY_SALARY * 0.85)

    # --- Analyze Yesterday's Opponent Bids ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    # --- Determine Base Bid ---
    # Start with a moderate bid, adjusted by my HP
    base_bid = DAILY_SALARY * 0.5
    if my_hp > 7: # High HP, can afford to be more conservative
        base_bid = DAILY_SALARY * 0.45
    elif my_hp <= 5: # Medium-low HP, need to be more aggressive
        base_bid = DAILY_SALARY * 0.6

    # --- Adjust bid based on Opponent's Yesterday's Activity ---
    target_bid = base_bid

    if max_yesterday_bid > 0:
        if max_yesterday_bid >= DAILY_SALARY * 0.8: # Very high competition yesterday
            if my_hp > 6: # Good HP, try to match closely
                target_bid = max(target_bid, max_yesterday_bid * 0.98)
            else: # Need water more urgently
                target_bid = max(target_bid, max_yesterday_bid + 2.0)
        elif max_yesterday_bid >= DAILY_SALARY * 0.6: # Moderate competition yesterday
            target_bid = max(target_bid, max_yesterday_bid + 1.0)
        else: # Low competition yesterday
            target_bid = max(target_bid, max_yesterday_bid + 0.5)

    # --- Adjust bid based on Supply and Days Left ---
    if supply <= 18: # Low supply, competition likely higher
        target_bid *= 1.05
    elif supply >= 22: # High supply, can try to save
        target_bid *= 0.95

    # Late game aggression
    if days_left <= 3:
        # If I have good HP and sufficient budget, be very aggressive to secure win
        if my_hp > 5 and my_budget / days_left > DAILY_SALARY * 0.7:
            target_bid = max(target_bid, DAILY_SALARY * 0.85)
        else: # Just ensure survival
            target_bid = max(target_bid, DAILY_SALARY * 0.7)
    elif days_left <= 5: # Mid-late game
        target_bid = max(target_bid, DAILY_SALARY * 0.65)

    # --- Final Bid Calculation ---
    final_bid = min(my_budget, target_bid)
    
    # Ensure a minimum bid to always participate
    final_bid = max(final_bid, DAILY_SALARY * 0.05)

    # Ensure bid is always positive
    return max(0.01, final_bid)
"""
