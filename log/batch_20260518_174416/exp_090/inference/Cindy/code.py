# ============================================================
# Experiment: exp_090
# Agent: Cindy
# Source: exp_090
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

    # If I am the only one left, bid low to conserve budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Calculate total water demand for all alive players (including myself)
    total_water_demand = WATER_REQ
    for opp in alive_opponents:
        total_water_demand += opp['water_requirement']

    # --- Base bid calculation ---
    # Start with a default bid
    bid = DAILY_SALARY * 0.4 

    # --- HP-based adjustment (primary driver for survival) ---
    if my_status['hp'] <= 2: # Critical HP, bid very aggressively
        bid = DAILY_SALARY * 0.98 # Almost max budget to survive
    elif my_status['hp'] <= 4: # Low HP, bid aggressively
        bid = DAILY_SALARY * 0.8
    elif my_status['hp'] <= 6: # Medium HP, moderate bid
        bid = DAILY_SALARY * 0.6
    # Else (HP > 6), bid remains DAILY_SALARY * 0.4

    # --- Supply-demand adjustment ---
    # This adjusts the bid based on overall resource availability
    if day_context['supply'] < total_water_demand:
        # Shortage detected, increase bid
        bid *= 1.1 # Increase by 10%
        # Ensure a minimum bid if supply is very tight and I need water
        if my_status['hp'] <= 6: # If not super healthy, ensure a good bid
            bid = max(bid, DAILY_SALARY * 0.7)
    elif day_context['supply'] >= total_water_demand + WATER_REQ * 0.5 * num_alive_opponents: # Significant surplus
        # Abundant supply, can afford to bid lower
        bid *= 0.8 # Reduce by 20%
        bid = max(bid, DAILY_SALARY * 0.2) # Don't go too low, but aim for efficiency

    # --- Opponent trace adjustment (yesterday's bids) ---
    # This fine-tunes the bid based on opponent behavior
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_opp_bid = max(yesterday_bids)

        # If opponents bid high yesterday, we might need to match or slightly exceed
        if max_opp_bid >= DAILY_SALARY * 0.7: # They were very aggressive
            bid = max(bid, max_opp_bid + 2) # Try to slightly outbid them
        elif max_opp_bid >= DAILY_SALARY * 0.4: # They were moderately aggressive
            bid = max(bid, max_opp_bid + 1) # Just a small edge
        else: # Opponents bid low yesterday
            if day_context['supply'] >= total_water_demand + WATER_REQ: # And supply is ample
                # Try to get water cheaply, but still above their low bid to secure
                bid = max(bid, max_opp_bid + 0.5) 
                # Also cap it so we don't overbid if our base bid was already high due to HP
                if my_status['hp'] > 6: # Only if healthy, try to be really cheap
                    bid = min(bid, DAILY_SALARY * 0.3)
            else: # Supply is not ample, even if they bid low, competition might be higher today
                bid = max(bid, max_opp_bid + 2) # Ensure we beat their low bid

    # --- Final checks ---
    # Ensure bid is not less than a minimum value (e.g., 1)
    final_bid = max(1.0, bid) 
    
    # If HP is critical, ensure a very high minimum bid, overriding other factors if necessary
    if my_status['hp'] <= 2:
        final_bid = max(final_bid, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4:
        final_bid = max(final_bid, DAILY_SALARY * 0.75)


    # Ensure bid does not exceed available budget
    final_bid = min(my_status['budget'], final_bid)
    
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
    
    # Find alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid minimum to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Calculate target bid based on opponent's previous bids
    max_opp_bid_yesterday = 0.0
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            max_opp_bid_yesterday = max(max_opp_bid_yesterday, prev_trace['bid'])

    # Default bid if no previous opponent bids or to set a floor
    target_bid = DAILY_SALARY * 0.7 
    
    if max_opp_bid_yesterday > 0:
        # Try to outbid by a small margin
        target_bid = max_opp_bid_yesterday + 1.0 

    # Emergency bid if HP is low or I missed water yesterday
    emergency_bid = 0.0
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        # If critical, bid very high, potentially most of the budget
        emergency_bid = my_status['budget'] * 0.95 
        # Ensure it's at least a full salary if budget allows
        emergency_bid = max(emergency_bid, DAILY_SALARY * 1.0)
    
    # Combine target and emergency bid
    final_bid = max(target_bid, emergency_bid)

    # Sustainable budget calculation to ensure long-term survival
    remaining_days = EPISODE_DAYS - day_context['day'] + 1 # Include current day
    
    if remaining_days <= 1:
        sustainable_max_bid = my_status['budget']
    else:
        # Budget required to survive if I pay my_daily_salary every day
        budget_needed_for_survival = DAILY_SALARY * remaining_days
        
        if my_status['budget'] >= budget_needed_for_survival:
            # I have a surplus, I can afford to bid higher by distributing surplus
            surplus = my_status['budget'] - budget_needed_for_survival
            extra_per_day = surplus / remaining_days
            sustainable_max_bid = DAILY_SALARY + extra_per_day
            # Add a small buffer for aggressiveness, but ensure it doesn't exceed total budget
            sustainable_max_bid = min(sustainable_max_bid * 1.05, my_status['budget'])
        else:
            # I don't have enough budget for all remaining days at daily salary rate.
            # Cap at daily salary, or my current budget if even lower.
            sustainable_max_bid = DAILY_SALARY * 1.0
            sustainable_max_bid = min(sustainable_max_bid, my_status['budget'])

    # Cap the final_bid by the calculated sustainable_max_bid
    final_bid = min(final_bid, sustainable_max_bid)
    
    # Ensure bid is at least a minimum amount (e.g., 1.0)
    final_bid = max(final_bid, 1.0)

    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10 

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.2)

    base_bid = DAILY_SALARY * 0.65

    if my_hp <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4:
        base_bid = DAILY_SALARY * 0.85
    elif my_no_water_days > 0:
        base_bid = DAILY_SALARY * 0.75

    normalized_supply = (current_supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    scarcity_factor = 1 - normalized_supply
    base_bid += (DAILY_SALARY * 0.2) * scarcity_factor

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.7:
            if my_hp <= 4:
                base_bid = max(base_bid, highest_prev_bid * 1.05)
            else:
                base_bid = max(base_bid, highest_prev_bid * 1.01)
        elif highest_prev_bid > base_bid * 0.7:
            base_bid = max(base_bid, highest_prev_bid + 1.0)
    
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2:
        if my_budget > DAILY_SALARY * 1.5:
            base_bid = max(base_bid, DAILY_SALARY * 0.9)
        elif my_hp <= 3:
            base_bid = DAILY_SALARY * 0.99

    final_bid = min(my_budget, base_bid)

    return max(1.0, final_bid)
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

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.6

    if day_context['supply'] < 18:
        base_bid *= 1.15
    elif day_context['supply'] >= 22:
        base_bid *= 0.9

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid > base_bid * 1.2:
            base_bid = max(base_bid, highest_prev_bid + 5)
        elif highest_prev_bid < base_bid * 0.8:
            base_bid = min(base_bid, highest_prev_bid + 2)

        if all(bid < DAILY_SALARY * 0.4 for bid in yesterday_bids):
            base_bid = min(base_bid, DAILY_SALARY * 0.45)

    final_bid = base_bid

    if my_status['no_water_days'] > 0:
        final_bid = max(final_bid, DAILY_SALARY * 0.9)
    elif my_status['hp'] <= 2:
        final_bid = max(final_bid, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4:
        final_bid = max(final_bid, DAILY_SALARY * 0.75)
    else:
        if my_status['hp'] > 7 and day_context['supply'] >= 20 and (not yesterday_bids or max(yesterday_bids) < DAILY_SALARY * 0.7):
             final_bid *= 0.95

    final_bid = min(final_bid, my_status['budget'])
    final_bid = max(1.0, final_bid)

    current_day = day_context['day']
    if current_day >= EPISODE_DAYS - 2:
        if my_status['hp'] < 5:
            final_bid = min(my_status['budget'], DAILY_SALARY * 0.99)
        elif my_status['budget'] > DAILY_SALARY * 2:
            final_bid = max(final_bid, DAILY_SALARY * 0.7)

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
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    # Since supply (15-25) is always less than 2 * WATER_REQ (26), only one player can get water.
    # This means it's a direct competition to be the highest bidder to win the water.

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Initialize base bid aggressively, assuming strong competition from previous rounds' context
    # Alex and David often bid above 150.
    current_bid = DAILY_SALARY * 1.1 # Starting aggressive (165)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Aim to outbid the highest previous bid by a small margin
        current_bid = max(current_bid, highest_prev_bid + 5)
    
    # Adjust bid based on my health and recent water status
    if my_status['hp'] <= 2: # Critical HP, must win
        current_bid = max(current_bid, DAILY_SALARY * 1.25) # Bid very aggressively (187.5)
    elif my_status['no_water_days'] > 0: # Missed water yesterday, need to win today
        current_bid = max(current_bid, DAILY_SALARY * 1.15) # Bid strongly (172.5)
    
    # Ensure bid does not exceed available budget
    final_bid = min(my_status['budget'], current_bid)

    # Ensure bid is at least a minimal amount to be considered
    final_bid = max(final_bid, 1.0) 

    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to secure water
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Determine a base bid, starting strong
    base_bid = DAILY_SALARY * 0.9 # 135

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Adjust base_bid based on yesterday's highest bid to stay competitive
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        base_bid = max(base_bid, highest_prev_bid + 1.0)

    # Final bid calculation, adjusted for HP and game stage
    bid = base_bid

    CRITICAL_HP_THRESHOLD = 3
    days_left = EPISODE_DAYS - day_context['day']

    if my_status['hp'] <= CRITICAL_HP_THRESHOLD: # High danger, must win
        if days_left <= 2: # End game push, bid very high
            bid = max(bid, DAILY_SALARY * 1.6) # 240
        else: # Mid-game critical HP, bid aggressively
            bid = max(bid, DAILY_SALARY * 1.3) # 195
    elif my_status['no_water_days'] >= 1: # Missed water yesterday, need to be more aggressive today
        bid = max(bid, DAILY_SALARY * 1.1) # 165
    else: # HP is good, but still competitive for water
        # Given supply range (15-25) and my WATER_REQ (13), only one 'my-sized' slot is available.
        # Therefore, always bid strong to secure water even with good HP.
        bid = max(bid, DAILY_SALARY * 1.0) # At least 150

    # Ensure bid does not exceed current budget
    bid = min(bid, my_status['budget'])

    # Ensure bid is non-negative
    bid = max(0.0, bid)

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

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If I'm the only one left, bid just enough to survive
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Collect previous bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid
    base_bid = DAILY_SALARY * 0.55 # Default moderate bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # Strategy 1: React to high bids (e.g., Alex-like behavior)
        if highest_prev_bid >= DAILY_SALARY * 0.8: # High competition threshold
            if my_hp > 3 and my_budget > DAILY_SALARY * 2: # Healthy and good budget, try to conserve
                bid = DAILY_SALARY * 0.4
            else: # Need water or low budget, must compete
                bid = highest_prev_bid + 5.0 # Bid slightly above
                bid = max(bid, DAILY_SALARY * 0.7) # Ensure a minimum competitive bid
        
        # Strategy 2: React to moderate/low bids (e.g., Bob-like or non-desperate opponents)
        else:
            bid = highest_prev_bid + 10.0 # Bid a bit higher to secure win
            bid = max(bid, DAILY_SALARY * 0.4) # Ensure a minimum bid
    else:
        # No previous bids (e.g., Day 1)
        bid = base_bid

    # Critical survival logic: If HP is low or no water for a day, bid aggressively
    if my_hp <= 2 or my_no_water_days >= 1:
        bid = max(bid, DAILY_SALARY * 0.9) # Ensure a high bid for survival
        # If it's late in the game and I'm very desperate, bid even higher
        if current_day >= int(EPISODE_DAYS * 0.7) and my_hp <= 1:
            bid = max(bid, DAILY_SALARY * 1.1)

    # Ensure bid does not exceed budget
    bid = min(bid, my_budget)
    
    # Cap bid to prevent excessive spending, unless truly desperate
    if my_hp > 1: # If not critically low HP, cap the bid
        bid = min(bid, DAILY_SALARY * 1.2) # Don't bid more than 120% of daily salary
    
    # Ensure bid is at least 1.0 to be a valid bid
    bid = max(1.0, bid)

    return bid
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
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    yesterday_bids_from_survivors = []
    yesterday_bids_from_all_alive = []

    strong_opponent_ids = ["Bob", "David"]

    for opp_id, opp in opponents_status.items():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids_from_all_alive.append(prev['bid'])
            if opp_id in strong_opponent_ids:
                yesterday_bids_from_survivors.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.7 

    if yesterday_bids_from_survivors:
        highest_strong_bid = max(yesterday_bids_from_survivors)
        base_bid = max(base_bid, highest_strong_bid * 1.05)
    elif yesterday_bids_from_all_alive:
        highest_all_bid = max(yesterday_bids_from_all_alive)
        base_bid = max(base_bid, highest_all_bid * 1.02)

    if my_hp <= 26:
        base_bid = max(base_bid, DAILY_SALARY * 0.95)
    elif my_hp <= 39:
        base_bid = max(base_bid, DAILY_SALARY * 0.85)
    
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif remaining_days <= 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    if current_supply <= 18:
        base_bid *= 1.05
    elif current_supply >= 22:
        base_bid *= 0.98

    final_bid = base_bid

    final_bid = min(my_budget, final_bid)
    
    if my_budget <= DAILY_SALARY * 0.1 and my_budget > 0 and my_hp <= 39:
        final_bid = my_budget
    elif my_budget > 0 and final_bid < DAILY_SALARY * 0.1:
        final_bid = max(final_bid, DAILY_SALARY * 0.1)
    elif my_budget == 0:
        final_bid = 0.0

    return round(final_bid, 2)
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
    days_left = EPISODE_DAYS - day_context['day']

    if not alive_opponents:
        # If no opponents, bid a low but sufficient amount to get water
        # Cindy will get min(supply, WATER_REQ) = 13 water if she bids anything > 0.
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    bid = 0.0

    # Critical survival mode: If HP is very low, bid almost all budget
    if my_status['hp'] <= 1:
        return my_status['budget']
    
    # Low HP, but not critical, bid very aggressively
    if my_status['hp'] <= 3:
        if days_left <= 3: # End game, high stakes
            bid = min(my_status['budget'], DAILY_SALARY * 1.05) # Try to go slightly above salary
        else:
            bid = min(my_status['budget'], DAILY_SALARY * 0.95)
        return bid

    # General competitive bidding strategy
    # Since only one agent can typically get their full water requirement, we must be aggressive.
    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.9: # Opponents are already very aggressive
            if my_status['hp'] > 5: # Good HP, try to match or slightly exceed, but don't deplete budget too fast
                bid = max(DAILY_SALARY * 0.85, highest_prev_bid + 1.0)
            else: # Moderate HP, be more aggressive
                bid = max(DAILY_SALARY * 0.9, highest_prev_bid + 2.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.7: # Moderate to high bids
            bid = max(DAILY_SALARY * 0.8, highest_prev_bid + 3.0)
        else: # Lower bids, try to win definitively
            bid = max(DAILY_SALARY * 0.85, highest_prev_bid + 5.0)
    else:
        # No previous high bids (e.g., Day 1 or opponents didn't bid), use a strong default
        bid = DAILY_SALARY * 0.85 # Start strong

    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], bid)
    
    # Ensure a minimal bid if budget allows to participate
    if final_bid < 1.0 and my_status['budget'] > 0:
        final_bid = 1.0
        
    # Ensure bid is not negative
    final_bid = max(0.0, final_bid)
        
    return final_bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, 1.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid: Strong bid reflecting high competition due to tight supply
    bid = DAILY_SALARY * 0.75 # 112.5

    # Aggressively bid if HP is low or I missed water yesterday
    if my_hp <= 2: # Critical HP, must get water
        bid = DAILY_SALARY * 0.95 # 142.5
    elif my_hp <= 5 or my_no_water_days >= 1: # Low HP or missed water
        bid = DAILY_SALARY * 0.88 # 132.0

    # Adjust bid based on opponent's previous highest bid to stay competitive
    if highest_prev_bid > bid:
        bid = highest_prev_bid + 2.0 # Slightly outbid the highest opponent from yesterday

    # Adjust bid based on supply scarcity
    if current_supply <= WATER_REQ + 5: # Supply is 15-18, very tight
        bid = max(bid, DAILY_SALARY * 0.9) # 135.0

    # Ensure bid does not exceed available budget
    bid = min(bid, my_budget)

    # Ensure a minimum substantial bid if I desperately need water
    if my_hp <= 5 or my_no_water_days >= 1:
        bid = max(bid, DAILY_SALARY * 0.6) # Ensure a substantial bid (90.0)

    # Ensure bid is always positive
    bid = max(bid, 0.1)

    return float(bid)
"""
