# ============================================================
# Experiment: exp_005
# Agent: Cindy
# Source: exp_005
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid - a percentage of daily salary
    base_bid = DAILY_SALARY * 0.4

    # Scenario 1: No active opponents
    if not alive_opponents:
        return min(my_status['budget'], base_bid) # Bid low but sufficient to get water

    # Calculate total water demand (including myself)
    total_water_demand = WATER_REQ + sum(opp['water_requirement'] for opp in alive_opponents)

    # Assess competition level based on supply vs demand
    is_competitive = day_context['supply'] < total_water_demand
    
    # Assess if supply is generally low (regardless of current demand)
    is_low_global_supply = day_context['supply'] <= (MIN_SUPPLY + (MAX_SUPPLY - MIN_SUPPLY) * 0.25) # e.g., <= 17.5

    current_bid = base_bid

    # Adjust bid based on my current HP (priority)
    if my_status['hp'] <= 1: # Critical HP
        current_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] == 2: # Very low HP
        current_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] == 3: # Low HP
        current_bid = DAILY_SALARY * 0.65
    else: # HP > 3, more flexible
        # Adjust base bid based on general competition and supply conditions
        if is_competitive or is_low_global_supply:
            current_bid = max(current_bid, DAILY_SALARY * 0.6) # Increase base bid for tough days
        else:
            current_bid = max(current_bid, DAILY_SALARY * 0.45) # Slightly higher than base for easier days

    # Look at yesterday's bids from opponents to further adjust
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were bidding very high yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.8: 
            if my_status['hp'] > 3: # My HP is good
                # If current conditions are easy despite high previous bids, try to save
                if not is_competitive and not is_low_global_supply:
                    current_bid = min(current_bid, DAILY_SALARY * 0.5)
                else: # Current conditions are still tough, match closely
                    current_bid = max(current_bid, highest_prev_bid * 0.95)
            else: # My HP is critical, must get water, bid higher than highest previous
                current_bid = max(current_bid, highest_prev_bid + 5)
        
        # If opponents were bidding moderately high
        elif highest_prev_bid >= DAILY_SALARY * 0.5: 
            if my_status['hp'] > 3: # My HP is good
                if is_competitive or is_low_global_supply: # Tough day, slightly exceed
                    current_bid = max(current_bid, highest_prev_bid + 2)
                else: # Easier day, try to get it cheaper
                    current_bid = max(current_bid, highest_prev_bid * 0.9)
            else: # My HP is critical, ensure I exceed
                current_bid = max(current_bid, highest_prev_bid + 5)

        # If opponents were bidding low
        else:
            if my_status['hp'] > 3: # My HP is good
                if not is_competitive and not is_low_global_supply: # Very easy day, bid low
                    current_bid = min(current_bid, DAILY_SALARY * 0.3)
                else: # Still some competition/low supply, slightly above lowest
                    current_bid = max(current_bid, highest_prev_bid + 1)
            # If HP is critical, the HP-based bid already takes precedence

    # Ensure bid is within budget and positive
    final_bid = min(current_bid, my_status['budget'])
    final_bid = max(1.0, final_bid) # Minimum bid of 1.0
\    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to save budget.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    total_water_needed_by_all = WATER_REQ # Start with my requirement
    
    for opp in alive_opponents:
        total_water_needed_by_all += opp['water_requirement']
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # --- Base bid calculation ---
    current_bid = DAILY_SALARY * 0.5 # Default moderate bid

    # Adjust based on yesterday's highest bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest previous bid was very high, be aggressive.
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            current_bid = max(current_bid, highest_prev_bid + 2.0) # Outbid slightly
        # If previous bid was moderate, outbid slightly.
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            current_bid = max(current_bid, highest_prev_bid + 1.5)
        # Otherwise, bid conservatively but above previous.
        else:
            current_bid = max(current_bid, highest_prev_bid + 0.5)
    
    # --- Adjust bid based on supply scarcity ---
    # If supply is less than total demand, competition is high.
    available_slots = int(day_context['supply'] // WATER_REQ)
    num_players_alive = len(alive_opponents) + 1 # Including myself
    
    if available_slots < num_players_alive:
        # More players than available water slots, so competition is fierce.
        # Increase bid based on how many players might miss out.
        scarcity_premium = (num_players_alive - available_slots) * (DAILY_SALARY * 0.05)
        current_bid += scarcity_premium
            
    # --- HP-based adjustment (overrides other logic if critical) ---
    if my_status['hp'] <= 2: # Critical HP: Must get water
        current_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP: Strong need for water
        current_bid = max(current_bid, DAILY_SALARY * 0.8) # Ensure high bid if not already high

    # --- Final checks ---
    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], current_bid)
    # Ensure a minimum bid to stay in the game if healthy and not desperate
    final_bid = max(final_bid, DAILY_SALARY * 0.3) 

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.55

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                base_bid = DAILY_SALARY * 0.6
            else:
                base_bid = DAILY_SALARY * 0.95
        else:
            base_bid = max(DAILY_SALARY * 0.5, average_prev_bid * 1.05)

    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.99
    elif my_status['no_water_days'] > 0:
        base_bid = DAILY_SALARY * 0.9

    if day_context['day'] >= EPISODE_DAYS - 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.75)

    total_water_needed = sum([o['water_requirement'] for o in alive_opponents] + [WATER_REQ])
    if day_context['supply'] < total_water_needed:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    final_bid = min(my_status['budget'], base_bid)
    return max(0.0, final_bid)
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

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine bid based on opponent behavior and my status
    bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents are bidding very high
        if highest_prev_bid >= DAILY_SALARY * 0.85: # 127.5
            if my_status['hp'] > 3 and day_context['day'] < EPISODE_DAYS - 2: # Not critical days, HP is good
                bid = DAILY_SALARY * 0.6 # 90.0 - try to conserve but stay competitive
            else:
                # HP is low or it's a critical day, bid very high to survive
                bid = DAILY_SALARY * 0.95 # 142.5
        else:
            # Opponents are not extremely aggressive, bid slightly above their highest
            # but ensure it's at least a moderate bid
            bid = max(DAILY_SALARY * 0.6, highest_prev_bid + 2.0) # 90.0, or highest_prev_bid + 2.0
    else:
        # No yesterday bids (e.g., first day or all previous bidders died)
        if my_status['hp'] <= 3 or day_context['day'] >= EPISODE_DAYS - 2: # Low HP or critical days
            bid = DAILY_SALARY * 0.9 # 135.0
        else:
            bid = DAILY_SALARY * 0.7 # 105.0 - moderate initial bid

    # Ensure bid doesn't exceed budget
    final_bid = min(my_status['budget'], bid)

    # Ensure bid is at least 1 if budget allows and we desperately need water
    if final_bid == 0 and my_status['budget'] > 0 and my_status['hp'] <= 5:
        final_bid = 1.0

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

    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    estimated_total_demand = WATER_REQ
    for opp in alive_opponents:
        estimated_total_demand += opp['water_requirement']

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    base_bid = DAILY_SALARY * 0.8

    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        base_bid = DAILY_SALARY * 1.05
        if max_prev_bid > 0:
            base_bid = max(base_bid, max_prev_bid + 5.0)
    elif current_day >= EPISODE_DAYS - 2:
        base_bid = DAILY_SALARY * 1.0
        if max_prev_bid > 0:
            base_bid = max(base_bid, max_prev_bid + 3.0)
    else:
        if num_alive_opponents > 0 and current_supply <= estimated_total_demand:
            base_bid = DAILY_SALARY * 0.9
            if max_prev_bid > 0:
                base_bid = max(base_bid, max_prev_bid + 2.0)
        elif num_alive_opponents == 0:
            base_bid = DAILY_SALARY * 0.1
        else:
            if max_prev_bid > 0:
                base_bid = max(DAILY_SALARY * 0.7, max_prev_bid + 1.0)
            else:
                base_bid = DAILY_SALARY * 0.75

    final_bid = min(my_status['budget'], base_bid)
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no active opponents, bid low but enough to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid
    base_bid = DAILY_SALARY * 0.5 # 75.0

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest bid was very high, we need to be competitive
        if highest_prev_bid >= DAILY_SALARY * 0.8: # 120.0
            bid = highest_prev_bid + 5.0 # Try to outbid
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # 75.0
            bid = highest_prev_bid + 2.0 # Slightly outbid
        else:
            bid = max(base_bid, highest_prev_bid + 1.0) # Ensure a reasonable floor
    else:
        # No previous bids from alive opponents, or first day
        bid = base_bid

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP
        bid = max(bid, DAILY_SALARY * 0.95) # 142.5
    elif my_status['hp'] <= 4: # Low HP
        bid = max(bid, DAILY_SALARY * 0.8) # 120.0
    elif my_status['hp'] <= 6 and my_status['no_water_days'] > 0: # Missed water recently
        bid = max(bid, DAILY_SALARY * 0.85) # 127.5

    # Adjust bid based on supply scarcity
    current_supply = day_context['supply']
    
    # If supply is very tight (e.g., just enough for me or slightly more)
    if current_supply <= WATER_REQ + 5: # Supply 15-18.0
        bid += DAILY_SALARY * 0.1 # Increase bid by 15.0
    elif current_supply >= MAX_SUPPLY - 5: # Supply 20-25.0 (more abundant)
        bid -= DAILY_SALARY * 0.05 # Decrease bid by 7.5

    # Ensure bid is within budget and has a minimum value
    final_bid = min(my_status['budget'], max(1.0, bid))

    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    CRITICAL_HP_THRESHOLD = 2  # If HP <= 2, bid very aggressively
    SURVIVAL_HP_THRESHOLD = 5  # If HP <= 5, bid aggressively
    HIGH_COMPETITION_SUPPLY_THRESHOLD = WATER_REQ * 1.5  # If supply is below this, competition is high

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimal to save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Base bid, adjusted by HP and supply conditions
    my_current_bid = DAILY_SALARY * 0.5  # Default moderate bid

    # Adjust bid based on my HP
    if my_status['hp'] <= CRITICAL_HP_THRESHOLD:
        my_current_bid = DAILY_SALARY * 0.98  # Must get water
    elif my_status['hp'] <= SURVIVAL_HP_THRESHOLD:
        my_current_bid = DAILY_SALARY * 0.85  # High urgency
    elif my_status['no_water_days'] > 0:  # Missed water yesterday
        my_current_bid = max(my_current_bid, DAILY_SALARY * 0.75)

    # Adjust bid based on supply scarcity
    if day_context['supply'] < HIGH_COMPETITION_SUPPLY_THRESHOLD:
        # If supply is low, competition will be fierce
        my_current_bid = max(my_current_bid, DAILY_SALARY * 0.7)
        # If supply is extremely low (only one person can possibly get water)
        # e.g. supply 15, 16, 17... (WATER_REQ is 13)
        if day_context['supply'] < WATER_REQ + 2 and num_alive_opponents >= 1:
            my_current_bid = max(my_current_bid, DAILY_SALARY * 0.9)


    # Incorporate opponents' previous bids for dynamic adjustment
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If highest previous bid was very high, and I need water, match/exceed
        if highest_prev_bid > DAILY_SALARY * 0.75 and (my_status['hp'] <= SURVIVAL_HP_THRESHOLD or day_context['supply'] < HIGH_COMPETITION_SUPPLY_THRESHOLD):
            my_current_bid = max(my_current_bid, highest_prev_bid + 2.0)  # Bid slightly higher

        # If highest previous bid was moderate, and I'm not desperate, try to outbid slightly
        elif highest_prev_bid > DAILY_SALARY * 0.4 and my_status['hp'] > SURVIVAL_HP_THRESHOLD:
            my_current_bid = max(my_current_bid, highest_prev_bid + 1.0)
        
        # If highest previous bid was low, and I'm not desperate, try to get it cheaper
        elif highest_prev_bid < DAILY_SALARY * 0.4 and my_status['hp'] > CRITICAL_HP_THRESHOLD:
            my_current_bid = min(my_current_bid, highest_prev_bid + 1.0)
            my_current_bid = max(my_current_bid, DAILY_SALARY * 0.2)  # Don't bid too low if others are bidding low

    # Ensure a minimum bid if there are opponents, to stay competitive
    my_current_bid = max(my_current_bid, DAILY_SALARY * 0.3 if num_alive_opponents > 0 else DAILY_SALARY * 0.1)

    # Final check: Don't bid more than budget, and bid must be positive
    final_bid = min(my_current_bid, my_status['budget'])
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid very low to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    current_day = day_context['day']

    # Determine a base bid based on HP
    bid_amount = DAILY_SALARY * 0.5 # Default moderate bid

    if my_current_hp <= 2: # Critical HP
        bid_amount = DAILY_SALARY * 0.95
        # If it's late in the game and budget allows, bid even higher
        if current_day >= EPISODE_DAYS - 2 and my_current_budget > DAILY_SALARY * 1.5:
            bid_amount = min(my_current_budget, DAILY_SALARY * 1.1)
    elif my_current_hp <= 4: # Low HP
        bid_amount = DAILY_SALARY * 0.8
    else: # Healthy HP (5-10)
        bid_amount = DAILY_SALARY * 0.6

    # Adjust bid based on yesterday's highest opponent bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.85: # Opponents bid very high (>= 127.5)
            if my_current_hp > 4: # Healthy HP (>4 means 5-10)
                # Conserve budget if healthy, let opponents exhaust themselves
                bid_amount = min(bid_amount, DAILY_SALARY * 0.3)
            else: # Low or Critical HP (<=4)
                # Must compete, outbid the highest previous bid
                bid_amount = max(bid_amount, highest_prev_bid + 5.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # Opponents bid moderately high (90-127.5)
            # Try to outbid to secure water
            bid_amount = max(bid_amount, highest_prev_bid + 2.0)
        else: # Opponents bid low (<90)
            # Secure water efficiently
            bid_amount = max(bid_amount, highest_prev_bid + 1.0)

    # Ensure bid is not negative and does not exceed budget
    final_bid = max(0.1, min(my_current_budget, bid_amount))

    return final_bid
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

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to win
    if not alive_opponents:
        return min(my_budget, 1)

    # Calculate total water requirement for all alive agents (including myself)
    total_water_req = WATER_REQ
    for opp in alive_opponents:
        total_water_req += opp['water_requirement']

    # Analyze yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid strategy
    base_bid = DAILY_SALARY * 0.5

    # Adjust base bid based on current HP
    if my_hp <= 2: # Critical HP, bid aggressively
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP, bid quite aggressively
        base_bid = DAILY_SALARY * 0.8
    elif my_hp >= 8: # High HP, can afford to be more conservative
        base_bid = DAILY_SALARY * 0.4

    # Adjust bid based on day progression
    if current_day >= EPISODE_DAYS - 2: # Last two days, bid more aggressively to secure win
        base_bid = max(base_bid, DAILY_SALARY * 0.75)
        if my_hp <= 3: # Even more aggressive if HP is low towards the end
            base_bid = max(base_bid, DAILY_SALARY * 1.0)

    # Adjust bid based on supply vs demand
    # If supply is tight, competition will be higher
    if current_supply < total_water_req:
        base_bid *= 1.15 # Increase bid significantly
    # If supply is abundant, can bid lower
    elif current_supply >= total_water_req + WATER_REQ:
        base_bid *= 0.85 # Decrease bid

    # Adjust bid based on opponents' previous bids
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        if current_supply < total_water_req: # Tight supply, need to outbid
            # Bid slightly above max previous bid, but consider budget
            competitive_bid = max_prev_bid + (DAILY_SALARY * 0.15) # Add a small increment
            base_bid = max(base_bid, competitive_bid)
        else: # Abundant supply, try to get water cheaper
            # Bid slightly above average, but not too low to risk losing
            competitive_bid = avg_prev_bid + (DAILY_SALARY * 0.05)
            base_bid = min(base_bid, competitive_bid * 1.1) # Ensure it's not too low, but try to keep it down
            base_bid = max(base_bid, DAILY_SALARY * 0.2)

    # Final bid must be at least 1 and not exceed budget
    final_bid = max(1, base_bid)
    final_bid = min(final_bid, my_budget)

    # If I have very little budget left and it's not the last day, try to save if HP is good
    if my_budget < DAILY_SALARY * 0.3 and current_day < EPISODE_DAYS - 1 and my_hp > 3:
        final_bid = min(final_bid, my_budget * 0.5) # Try to save some budget

    return final_bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    TOTAL_DAYS = 10

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    remaining_days = TOTAL_DAYS - current_day + 1

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0
    average_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0

    base_bid = DAILY_SALARY * 0.5

    if my_hp <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4:
        base_bid = DAILY_SALARY * 0.8
    elif my_hp <= 6:
        base_bid = DAILY_SALARY * 0.65
    else:
        base_bid = DAILY_SALARY * 0.45

    if remaining_days <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif remaining_days <= 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.7)

    num_slots = int(current_supply // WATER_REQ)

    if num_slots == 0:
        return min(my_budget, DAILY_SALARY * 0.1)
    elif num_slots == 1:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    elif num_slots == 2 and num_alive_opponents >= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.6)
    elif num_slots > num_alive_opponents + 1:
        base_bid = min(base_bid, DAILY_SALARY * 0.3)

    if highest_prev_bid > 0:
        if my_hp <= 3 or my_no_water_days > 0:
            base_bid = max(base_bid, highest_prev_bid * 1.05)
        elif highest_prev_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, highest_prev_bid * 1.02)
        elif average_prev_bid > DAILY_SALARY * 0.4:
            base_bid = max(base_bid, average_prev_bid + 5)

    final_bid = min(my_budget, base_bid)

    if my_hp <= 5 or my_no_water_days > 0:
        final_bid = max(final_bid, DAILY_SALARY * 0.2)

    final_bid = max(0.0, final_bid)

    return final_bid
"""
