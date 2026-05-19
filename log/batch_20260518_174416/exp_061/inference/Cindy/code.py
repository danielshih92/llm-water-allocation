# ============================================================
# Experiment: exp_061
# Agent: Cindy
# Source: exp_061
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    CRITICAL_HP_THRESHOLD = 3  # If HP is 3 or less, bid aggressively
    HIGH_HP_THRESHOLD = 7  # If HP is 7 or more, can be more conservative

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Calculate total water demand accurately
    total_water_demand = WATER_REQ  # My requirement
    for opp in alive_opponents:
        total_water_demand += opp['water_requirement']

    # Base bid: a fraction of daily salary
    base_bid = DAILY_SALARY * 0.5

    # Analyze opponent's previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    max_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    # Strategy based on HP and supply
    bid = base_bid # Default to base bid

    if my_current_hp <= CRITICAL_HP_THRESHOLD:
        # Critical HP: Bid very high to ensure water
        bid = DAILY_SALARY * 0.95
        # If max opponent bid was high, try to slightly exceed it if affordable
        if max_yesterday_bid > 0 and bid <= max_yesterday_bid + 5:
            bid = max(bid, max_yesterday_bid + 5.0)

    elif current_supply < total_water_demand:
        # Supply is tight, increase bid
        bid = DAILY_SALARY * 0.7
        # If max opponent bid was high, try to slightly exceed it
        if max_yesterday_bid > 0 and bid <= max_yesterday_bid + 2:
            bid = max(bid, max_yesterday_bid + 2.0)

    else:
        # Moderate HP, moderate/abundant supply
        if max_yesterday_bid > 0:
            # If opponents bid high yesterday, bid slightly above their max to secure water
            if max_yesterday_bid >= DAILY_SALARY * 0.7:
                bid = max_yesterday_bid + 1.0 # Try to outbid by a small margin
            elif max_yesterday_bid >= DAILY_SALARY * 0.4:
                bid = max(base_bid, max_yesterday_bid + 0.5)
            # else: opponents bid low or 0, use base_bid (already assigned)

        # If my HP is high and supply is truly abundant, I can afford to be more conservative
        if my_current_hp >= HIGH_HP_THRESHOLD and current_supply > total_water_demand + WATER_REQ: 
            bid = min(bid, DAILY_SALARY * 0.4)

    # Ensure bid doesn't exceed budget
    final_bid = min(my_current_budget, bid)
    
    # Ensure bid is at least 1.0 if I need water or my HP is low
    if my_status['no_water_days'] > 0 or my_current_hp <= CRITICAL_HP_THRESHOLD:
        final_bid = max(1.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents are alive, bid minimally to get water and save budget.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # Determine base bid for non-critical situations
    base_bid = DAILY_SALARY * 0.5 # 75

    # Survival mode: If HP is critically low, bid very aggressively
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 1.05) # Bid slightly above daily salary for survival

    # If my HP is low but not critical, bid strongly
    if my_status['hp'] <= 4:
        # If there were high bids yesterday, be more aggressive
        if yesterday_bids and max(yesterday_bids) >= DAILY_SALARY * 0.7: # 105
            return min(my_status['budget'], max(DAILY_SALARY * 0.9, max(yesterday_bids) + 5))
        return min(my_status['budget'], DAILY_SALARY * 0.8) # 120

    # General competition strategy based on yesterday's bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest previous bid was very high, assume high competition
        if highest_prev_bid >= DAILY_SALARY * 0.85: # 127.5
            # If supply is low relative to active players, bid even higher
            if int(day_context['supply'] // WATER_REQ) < num_alive_opponents + 1:
                return min(my_status['budget'], max(highest_prev_bid + 5, DAILY_SALARY * 0.9))
            else: # Enough for everyone, but still high bids, maybe someone is overbidding
                return min(my_status['budget'], max(highest_prev_bid + 2, DAILY_SALARY * 0.75))
        
        # If highest previous bid was moderate
        if highest_prev_bid >= DAILY_SALARY * 0.6: # 90
            # Bid slightly above it to secure water, but not overpay
            return min(my_status['budget'], max(base_bid, highest_prev_bid + 1))
        
        # If highest previous bid was low, still bid a reasonable amount
        return min(my_status['budget'], max(base_bid, highest_prev_bid + 1))

    # If no previous bids (e.g., first day or opponents did not bid) or no strong signal
    # Adjust based on supply and number of competitors
    num_slots = int(day_context['supply'] // WATER_REQ)
    if num_slots < num_alive_opponents + 1: # High competition
        return min(my_status['budget'], DAILY_SALARY * 0.7) # 105
    else: # Low competition, everyone can get water
        return min(my_status['budget'], DAILY_SALARY * 0.45) # 67.5
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
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    if my_status['hp'] <= 4 and day_context['day'] >= EPISODE_DAYS - 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.7

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            base_bid = max(base_bid, highest_prev_bid + 2)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.65)
            
    if day_context['supply'] <= (WATER_REQ + 2):
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    elif day_context['supply'] >= (WATER_REQ * 1.5):
        if my_status['hp'] > 5:
            base_bid = min(base_bid, DAILY_SALARY * 0.7)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.75)

    final_bid = min(my_status['budget'], base_bid)

    if final_bid <= 0 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.1)
    elif final_bid < DAILY_SALARY * 0.1 and my_status['budget'] >= DAILY_SALARY * 0.1:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.1)

    return final_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_competitors = len(alive_opponents) + 1 # Include myself

    # If I'm the only one left, bid just enough to survive
    if num_alive_competitors == 1:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    current_day = day_context['day']
    current_supply = day_context['supply']

    # Collect yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid based on yesterday's highest bid
    # If no previous bids (e.g., Day 1 or all previous bidders died), use a default
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
    else:
        max_prev_bid = DAILY_SALARY * 0.5 # A reasonable mid-range bid for Day 1

    # Adjust base bid based on supply pressure
    supply_pressure_factor = 1.0
    if (MAX_SUPPLY - MIN_SUPPLY) > 0: # Avoid division by zero
        # Higher pressure (factor > 1.0) when supply is closer to MIN_SUPPLY
        supply_pressure_factor = 1.0 + (1.0 - (current_supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)) * 0.3
    
    adjusted_base_bid = max_prev_bid * supply_pressure_factor

    my_bid = adjusted_base_bid

    # Critical HP: Bid very high to ensure survival
    if my_status['hp'] <= 2:
        my_bid = max(my_bid, DAILY_SALARY * 0.95) 
    # Low HP: Bid aggressively
    elif my_status['hp'] <= 5:
        my_bid = max(my_bid, DAILY_SALARY * 0.75) 
    # Healthy HP: Can be more strategic
    else:
        # Calculate total water requirement for all alive competitors (including myself)
        total_water_needed_if_all_want_full_req = WATER_REQ * num_alive_competitors
        if current_supply >= total_water_needed_if_all_want_full_req:
            # Abundant supply, can be more conservative, but still competitive
            my_bid = min(my_bid, max(DAILY_SALARY * 0.4, max_prev_bid * 0.9))
        else:
            # Supply is tight, competition is high, try to win
            my_bid = max(my_bid, max_prev_bid + (DAILY_SALARY * 0.05)) # Bid slightly above previous high

    # Consider the day: later days might mean more desperation
    # Increase bid pressure in the last 30% of days if HP is not critically high
    if current_day >= int(EPISODE_DAYS * 0.7) and my_status['hp'] <= 7:
        my_bid = max(my_bid, DAILY_SALARY * 0.8)

    # Ensure bid does not exceed my budget
    my_bid = min(my_status['budget'], my_bid)

    # Ensure bid is at least a minimum positive amount if budget allows
    if my_status['budget'] > 0:
        my_bid = max(my_bid, 1.0)
    else:
        my_bid = 0.0 # Cannot bid if budget is 0

    return my_bid
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

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid_amount = DAILY_SALARY * 1.0

    if my_status['hp'] <= 3 or my_status['no_water_days'] > 0:
        bid_amount = DAILY_SALARY * 1.9
    elif my_status['hp'] <= 5:
        bid_amount = DAILY_SALARY * 1.3

    if day_context['supply'] <= WATER_REQ + 4:
        bid_amount *= 1.1
    elif day_context['supply'] >= WATER_REQ * 1.8:
        bid_amount *= 0.9

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 1.5:
            bid_amount = max(bid_amount, highest_prev_bid * 1.05)
        elif highest_prev_bid > bid_amount * 0.9:
            bid_amount = max(bid_amount, highest_prev_bid + 5)

    final_bid = min(my_status['budget'], bid_amount)
    final_bid = max(0.0, final_bid)

    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days == 0:
        if my_status['hp'] >= WATER_REQ:
            final_bid = min(my_status['budget'], DAILY_SALARY * 0.1)
        else:
            final_bid = my_status['budget']

    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Calculate available water slots based on supply and my requirement
    available_slots = int(day_context['supply'] // WATER_REQ)
    if available_slots == 0: # If supply is less than my requirement, assume 1 slot for competitive bidding
        available_slots = 1

    current_day = day_context['day']

    # Base bid strategy
    bid = DAILY_SALARY * 0.7 # Default moderate bid

    # Adjust bid based on HP
    if my_status['hp'] <= 2: # Critical HP, must win
        bid = max(highest_prev_bid + 15, DAILY_SALARY * 1.25) # Very aggressive
    elif my_status['hp'] <= 5: # Low HP, need water
        bid = max(highest_prev_bid + 10, DAILY_SALARY * 1.0) # Aggressive
    else: # Healthy HP
        # Adjust based on supply and competition
        if day_context['supply'] <= WATER_REQ: # Only one slot possible or very tight
            bid = max(highest_prev_bid + 8, DAILY_SALARY * 0.9) # Highly competitive
        elif available_slots <= num_alive_opponents: # Fewer slots than active opponents
            bid = max(highest_prev_bid + 5, DAILY_SALARY * 0.85) # Competitive
        elif available_slots > num_alive_opponents + 1 and my_status['hp'] > 8: # Ample supply and healthy
            bid = max(DAILY_SALARY * 0.6, highest_prev_bid * 0.9) # Conserve budget, slightly less than highest if good
        else: # Normal conditions
            bid = max(highest_prev_bid + 2, DAILY_SALARY * 0.75) # Moderate, slightly above previous high

    # Further adjust for late game pressure
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        bid = max(bid, DAILY_SALARY * 1.05) # Be very aggressive at the end

    # Ensure bid doesn't exceed budget
    final_bid = min(my_status['budget'], bid)

    # Ensure a positive bid if I need water and have budget
    if my_status['hp'] < 10 and final_bid < DAILY_SALARY * 0.1 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.15) # Ensure a minimum bid if not full HP

    # Ensure bid is not negative
    final_bid = max(0.0, final_bid)

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

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid
    bid = DAILY_SALARY * 0.5

    # Survival mode: If HP is very low, bid aggressively
    if my_hp <= 1:
        bid = min(my_budget, DAILY_SALARY * 0.95)
    elif my_no_water_days >= 1: # If I missed water yesterday
        bid = min(my_budget, DAILY_SALARY * 0.9)
    elif my_hp <= 3 and current_day > EPISODE_DAYS / 2: # Mid-late game low hp
        bid = min(my_budget, DAILY_SALARY * 0.85)

    # Analyze yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Adjust bid based on opponent's previous high bids
    if highest_prev_bid > DAILY_SALARY * 0.7:
        if my_hp <= 2 or my_no_water_days >= 1:
            bid = min(my_budget, max(bid, highest_prev_bid + 5))
        else:
            bid = min(my_budget, max(bid, highest_prev_bid + 1))
    elif highest_prev_bid > DAILY_SALARY * 0.4:
        if my_hp <= 3:
            bid = min(my_budget, max(bid, highest_prev_bid + 2))
        else:
            bid = min(my_budget, max(bid, highest_prev_bid + 0.5))

    # Adjust bid based on supply and number of competitors
    if current_supply < 2 * WATER_REQ and num_alive_opponents >= 1:
        if my_hp <= 2 or my_no_water_days >= 1:
            bid = min(my_budget, max(bid, DAILY_SALARY * 0.9))
        else:
            bid = min(my_budget, max(bid, DAILY_SALARY * 0.7))
    elif current_supply >= (num_alive_opponents + 1) * WATER_REQ:
        if my_hp > 5: # If healthy, try to bid lower
            bid = min(my_budget, max(bid * 0.8, DAILY_SALARY * 0.3))
        else: # Still need water, but can be slightly less aggressive
            bid = min(my_budget, max(bid * 0.9, DAILY_SALARY * 0.4))

    # End game strategy
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2:
        if my_hp > 0: 
            bid = min(my_budget, max(bid, DAILY_SALARY * 0.9))

    # Ensure bid is at least a minimum and does not exceed budget
    bid = max(0.1, bid)
    bid = min(bid, my_budget)

    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = 0.0

    # Determine base bid based on my HP and day context
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        base_bid = DAILY_SALARY * 1.25
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 1.1
    elif my_status['hp'] <= 6:
        base_bid = DAILY_SALARY * 1.0
    else:
        base_bid = DAILY_SALARY * 0.85

    # Adjust for late game pressure
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 3 and my_status['hp'] < remaining_days + 1:
        base_bid = max(base_bid, DAILY_SALARY * 1.3)
    elif remaining_days <= 5 and my_status['hp'] < remaining_days + 1:
        base_bid = max(base_bid, DAILY_SALARY * 1.15)

    # Adjust bid based on opponent's previous behavior
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 1.1:
            if my_status['hp'] <= 4:
                base_bid = max(base_bid, highest_prev_bid + 5)
            else:
                base_bid = max(base_bid, highest_prev_bid + 1)
        elif highest_prev_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, highest_prev_bid + 1)
        else:
            if my_status['hp'] <= 6:
                base_bid = max(base_bid, highest_prev_bid + 1)
            else:
                base_bid = max(base_bid, DAILY_SALARY * 0.7)

    # Ensure a minimum competitive bid
    bid = max(base_bid, DAILY_SALARY * 0.6)

    # Ensure bid does not exceed current budget
    bid = min(my_status['budget'], bid)

    # Ensure bid is non-negative
    bid = max(0.0, bid)

    return bid
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

    # Initial bid - a competitive base
    base_bid = DAILY_SALARY * 0.85

    # Adjust bid based on my health and no-water days
    # Critical state: low HP or missed water yesterday
    if my_status['no_water_days'] > 0 or my_status['hp'] <= WATER_REQ:
        base_bid = DAILY_SALARY * 1.2 # Very aggressive (180)
        if day_context['day'] == EPISODE_DAYS: # Last day, bid everything to survive
            base_bid = my_status['budget']
    elif my_status['hp'] <= WATER_REQ * 2: # Getting low on HP, but not critical yet
        base_bid = DAILY_SALARY * 1.0 # Ensure I get water (150)

    # React to yesterday's highest bid from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest previous bid was significant, ensure my bid is competitive
        if highest_prev_bid >= DAILY_SALARY * 0.8: # e.g., > 120
            # If my current base_bid is not higher, increase it
            if base_bid <= highest_prev_bid:
                base_bid = highest_prev_bid + 2.0 # Try to outbid by a small margin
            # If highest bid was very aggressive (above my salary), ensure I can compete
            if highest_prev_bid >= DAILY_SALARY:
                base_bid = max(base_bid, DAILY_SALARY * 1.1) # At least 165 to compete with Eric

    # Consider supply scarcity
    # If supply is less than what I need, it's extremely critical.
    # If supply is less than what all alive agents need (including me), competition is high.
    total_water_needed_by_all_alive = WATER_REQ + sum([o['water_requirement'] for o in alive_opponents])

    if day_context['supply'] < WATER_REQ: # Not enough water for me alone
        base_bid = max(base_bid, DAILY_SALARY * 1.3) # Extremely aggressive (195)
    elif day_context['supply'] < total_water_needed_by_all_alive: # Scarcity among all
        base_bid = max(base_bid, DAILY_SALARY * 1.05) # More aggressive (157.5)

    # If no opponents are alive, bid minimally to save budget
    if not alive_opponents:
        base_bid = DAILY_SALARY * 0.3 # Very cheap (45)

    # Final bid cannot exceed current budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure bid is at least 1 if I have budget and need water, to avoid bidding 0 accidentally
    if final_bid <= 0 and my_status['budget'] > 0 and my_status['hp'] > 0:
        final_bid = 1.0
    elif my_status['budget'] <= 0: # If no budget, bid 0
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
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no active opponents, bid very low to save budget
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.3)

    # Default bid if no strong pressure, slightly above half salary
    base_bid = DAILY_SALARY * 0.6

    # Adjust based on my health and no-water days
    if my_hp <= 3: # Critical HP
        base_bid = max(base_bid, DAILY_SALARY * 1.1)
        if my_no_water_days > 0: # Missed water and low HP
            base_bid = max(base_bid, DAILY_SALARY * 1.3)
    elif my_hp <= 6 and my_no_water_days > 0: # Low HP and missed water
        base_bid = max(base_bid, DAILY_SALARY * 0.9)

    # Adjust based on supply scarcity
    # Calculate how many full water requirements can be met
    num_agents_who_can_get_water = int(current_supply // WATER_REQ)
    total_agents_needing_water = len(alive_opponents) + 1

    if num_agents_who_can_get_water < total_agents_needing_water:
        # Supply is scarce, competition will be high
        if num_agents_who_can_get_water < total_agents_needing_water / 2: # Very scarce
            base_bid = max(base_bid, DAILY_SALARY * 1.0)
        else: # Moderately scarce
            base_bid = max(base_bid, DAILY_SALARY * 0.8)

    # React to yesterday's highest bid from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were aggressive yesterday, we need to be competitive
        if highest_prev_bid >= DAILY_SALARY * 0.9: # Very high previous bids
            base_bid = max(base_bid, highest_prev_bid * 1.05) # Slightly outbid
        elif highest_prev_bid >= DAILY_SALARY * 0.7: # High previous bids
            base_bid = max(base_bid, highest_prev_bid * 1.02) # Slightly outbid
        else: # Moderate previous bids, ensure we're above them
            base_bid = max(base_bid, highest_prev_bid + 5)

    # End game pressure
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last 2 days
        if my_hp <= 5: # Need to survive
            base_bid = max(base_bid, DAILY_SALARY * 1.2) # Bid very high
        elif my_budget > DAILY_SALARY * 3 and my_hp > 7: # If I have a good budget and HP, keep pressure
            base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif current_day == 1: # First day, establish presence, don't overspend immediately
        base_bid = min(base_bid, DAILY_SALARY * 0.8) # Cap initial bid unless critical

    # Ensure bid doesn't exceed budget
    final_bid = min(my_budget, base_bid)

    # Ensure a minimum bid to actually participate
    final_bid = max(1.0, final_bid)

    return final_bid
"""
