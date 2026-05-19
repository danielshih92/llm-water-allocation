# ============================================================
# Experiment: exp_026
# Agent: Cindy
# Source: exp_026
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_BID = 1

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return int(min(my_status['budget'], MIN_BID))

    # Determine base bid based on my HP
    if my_status['hp'] <= 2:
        current_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] == 3:
        current_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] == 4:
        current_bid = DAILY_SALARY * 0.65
    else:
        current_bid = DAILY_SALARY * 0.45

    # Collect opponent's previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_opp_bid = max(yesterday_bids)

        # React to high opponent bids
        if highest_prev_opp_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                current_bid = max(current_bid, highest_prev_opp_bid + 5)
            else:
                current_bid = max(current_bid, highest_prev_opp_bid + 10)
        # React to low opponent bids (only if my HP is good)
        elif highest_prev_opp_bid < DAILY_SALARY * 0.3:
            if my_status['hp'] > 4:
                current_bid = min(current_bid, highest_prev_opp_bid + 10)
                current_bid = max(current_bid, DAILY_SALARY * 0.1)

    # Consider overall supply scarcity
    total_water_required_by_all = WATER_REQ + sum(o['water_requirement'] for o in alive_opponents)
    current_supply = day_context['supply']

    if current_supply < total_water_required_by_all:
        shortfall_ratio = current_supply / total_water_required_by_all
        if shortfall_ratio < 0.7:
            if my_status['hp'] > 3:
                current_bid = max(current_bid, DAILY_SALARY * 0.7)
            else:
                current_bid = max(current_bid, DAILY_SALARY * 0.9)
        elif shortfall_ratio < 0.9:
            if my_status['hp'] > 3:
                current_bid = max(current_bid, DAILY_SALARY * 0.55)
            else:
                current_bid = max(current_bid, DAILY_SALARY * 0.75)
    else:
        if my_status['hp'] > 4:
            current_bid = min(current_bid, DAILY_SALARY * 0.3)

    final_bid = max(MIN_BID, current_bid)
    final_bid = min(my_status['budget'], final_bid)

    return int(final_bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10
    
    # Base bid: a competitive amount, similar to what David used to survive.
    # Given water scarcity (only 1 agent can get full water), bidding aggressively is key.
    bid_amount = DAILY_SALARY * 0.55 # Start with 82.5

    # Adjust bid based on my health and water deprivation
    if my_status['hp'] <= 2: # Critical HP, bid almost everything
        bid_amount = DAILY_SALARY * 0.98 # 147
    elif my_status['hp'] <= 5: # Low HP
        bid_amount = DAILY_SALARY * 0.85 # 127.5
    elif my_status['no_water_days'] > 0: # Missed water yesterday, need to get it today
        bid_amount = DAILY_SALARY * 0.75 # 112.5
    
    # Consider opponents' previous bids to react
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If the highest bid yesterday was high, we need to be competitive.
        # Especially if we are in need of water (low hp or missed water).
        if highest_prev_bid >= DAILY_SALARY * 0.7: # If highest bid was 105 or more
            if my_status['hp'] <= 8 or my_status['no_water_days'] > 0:
                bid_amount = max(bid_amount, highest_prev_bid + 5) # Try to outbid by a margin
            else:
                bid_amount = max(bid_amount, highest_prev_bid + 1) # Stay competitive
        elif highest_prev_bid >= DAILY_SALARY * 0.4: # If highest bid was 60 or more
            bid_amount = max(bid_amount, highest_prev_bid + 2) # Ensure we are above it

    # End-game aggression: if it's nearing the end and I'm still in it, push harder.
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days
        bid_amount = max(bid_amount, DAILY_SALARY * 0.9) # Be very aggressive

    # If no opponents are alive, bid minimally to save budget.
    if not alive_opponents:
        bid_amount = DAILY_SALARY * 0.1 # 15

    # Ensure the bid does not exceed current budget
    final_bid = min(my_status['budget'], bid_amount)

    # Ensure bid is non-negative
    final_bid = max(0.0, final_bid)

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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']

    eric_last_bid = None
    eric_alive = False
    for opp_id, opp_data in opponents_status.items():
        if opp_id == "Eric":
            eric_alive = opp_data['alive']
            if eric_alive:
                prev_trace = opp_data.get('previous_trace', {})
                if prev_trace and prev_trace.get('bid') is not None:
                    eric_last_bid = prev_trace['bid']
            break

    calculated_bid = 0.0

    if eric_alive:
        eric_effective_bid = eric_last_bid if eric_last_bid is not None else 121.5
        
        competitive_bid = eric_effective_bid + 5.0 
        
        competitive_bid = max(competitive_bid, DAILY_SALARY * 0.8)
        
        calculated_bid = min(competitive_bid, DAILY_SALARY * 0.93)
        
    else:
        calculated_bid = DAILY_SALARY * 0.65

    if my_hp <= 2:
        calculated_bid = DAILY_SALARY * 0.98
    elif my_hp <= 4:
        calculated_bid = max(calculated_bid, DAILY_SALARY * 0.9)

    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2:
        if my_hp >= 8:
            calculated_bid = min(calculated_bid, DAILY_SALARY * 0.85)
        else:
             calculated_bid = max(calculated_bid, DAILY_SALARY * 0.8)

    final_bid = min(my_budget, calculated_bid)

    final_bid = max(1.0, final_bid)

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

    # Base bid: Start moderately high, knowing Alex's past high bids.
    # Alex's average bid was ~84. My salary is 150.
    # A base of 0.6 * 150 = 90. This is higher than Alex's average.
    bid = DAILY_SALARY * 0.6 # 90.0

    # --- Step 1: React to my own urgent needs ---
    if my_status['hp'] <= 1: # Very critical
        bid = DAILY_SALARY * 0.95 # 142.5
    elif my_status['hp'] <= 3: # Critical
        bid = DAILY_SALARY * 0.85 # 127.5
    
    if my_status['no_water_days'] >= 2:
        bid = max(bid, DAILY_SALARY * 0.9) # 135.0

    # --- Step 2: React to opponent's previous bids ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If my HP is not critical, try to outbid opponents
        if my_status['hp'] > 3:
            if highest_prev_bid >= DAILY_SALARY * 0.7: # High pressure (e.g., > 105)
                bid = max(bid, highest_prev_bid + 6.0) # Slightly more aggressive outbid
            elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderate pressure (e.g., > 75)
                bid = max(bid, highest_prev_bid + 3.0) # Slightly outbid
            else: # Low pressure
                bid = max(bid, DAILY_SALARY * 0.55) # Ensure a decent bid (82.5)
        else: # My HP is critical (<=3), I am already bidding high, ensure I'm competitive
            bid = max(bid, highest_prev_bid + 3.0) # Ensure I am above the highest previous bid, even if I'm desperate

    # --- Step 3: Adjust for late game ---
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 3 and my_status['hp'] > 0: # Last few days, push harder if still alive
        bid = max(bid, DAILY_SALARY * 0.92) # 138

    # --- Step 4: Budget constraint and minimum bid ---
    bid = min(bid, my_status['budget'])
    bid = max(1.0, bid)

    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        # If no opponents, bid minimally to secure water, as supply is always sufficient.
        return min(my_status['budget'], 1.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid if no specific conditions apply
    base_bid = DAILY_SALARY * 0.55

    # High priority: If my HP is critically low, bid aggressively to survive.
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9)

    # React to yesterday's highest bid from opponents
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If opponents were very aggressive yesterday (e.g., highest bid >= 85% of daily salary)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # My HP is okay, try to save by underbidding
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            else: # My HP is low or moderate, must compete fiercely
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        # If opponents were moderately aggressive or less
        else:
            # Try to bid slightly above the highest previous bid to secure water,
            # ensuring it's at least a reasonable base amount (50% of daily salary).
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))

    # Fallback for Day 1 or if no previous bids were recorded for other reasons
    return min(my_status['budget'], base_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to get water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # --- Determine base bid based on my HP ---
    base_bid = DAILY_SALARY * 0.6 # Default healthy bid

    if my_status['hp'] <= 2: # Critical health, bid aggressively
        base_bid = DAILY_SALARY * 1.05
    elif my_status['hp'] <= 4: # Low health
        base_bid = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 7: # Moderate health
        base_bid = DAILY_SALARY * 0.75
    # Else, base_bid remains DAILY_SALARY * 0.6 for healthy HP

    # --- Adjust bid based on opponent's yesterday bids (previous_trace) ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    final_bid = base_bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If I'm low on HP, I must win, so bid above max_yesterday_bid
        if my_status['hp'] <= 4:
            final_bid = max(final_bid, highest_prev_bid + 5)
        # If highest_prev_bid was already high, ensure I'm competitive
        elif highest_prev_bid >= DAILY_SALARY * 0.8:
            final_bid = max(final_bid, highest_prev_bid + 2)
        # Otherwise, bid slightly above to try and win
        else:
            final_bid = max(final_bid, highest_prev_bid + 1)

    # --- Adjust bid based on supply ---
    # Water is always scarce, as 13 * 5 = 65, and max supply is 25.
    # If supply is very low, competition is even fiercer.
    if day_context['supply'] < WATER_REQ + 5: # e.g., supply < 18 (15, 16, 17)
        final_bid *= 1.05 # Increase bid by 5% due to high scarcity
    elif day_context['supply'] > WATER_REQ + 10: # e.g., supply > 23 (24, 25)
        final_bid *= 0.98 # Slightly reduce bid if supply is relatively better

    # Ensure bid doesn't exceed budget and is at least a minimal amount
    final_bid = min(my_status['budget'], final_bid)
    final_bid = max(final_bid, DAILY_SALARY * 0.1) # Ensure a minimum bid to participate

    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    my_bid = 0.0

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine bid based on my HP and opponent's highest previous bid
    if my_status['hp'] <= 2:  # Critical health
        my_bid = DAILY_SALARY * 0.95
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            my_bid = max(my_bid, highest_prev_bid + 5.0) # Bid aggressively to win
    elif my_status['hp'] <= 4: # Low health
        my_bid = DAILY_SALARY * 0.8
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            my_bid = max(my_bid, highest_prev_bid + 3.0) # Competitive bid
    else: # Healthy (HP > 4)
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            my_bid = max(DAILY_SALARY * 0.6, highest_prev_bid + 1.0) # Slightly above to win, conserve budget. Min base 0.6*salary
        else: # Healthy and no previous bids (e.g., Day 1 or no competitive bids from opponents)
            my_bid = DAILY_SALARY * 0.4 # Bid lower to save money if no immediate competition

    # Ensure bid doesn't exceed current budget or daily salary (as a practical cap)
    my_bid = min(my_bid, my_status['budget'], float(DAILY_SALARY))

    # Ensure bid is at least a nominal amount if budget allows, to avoid 0 bid unless necessary
    if my_bid <= 0 and my_status['budget'] > 0:
        my_bid = min(my_status['budget'], DAILY_SALARY * 0.1)
    elif my_bid <= 0: # If budget is 0 or less, bid 0.
        my_bid = 0.0

    return my_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_SUPPLY = 25.0
    MIN_SUPPLY = 15.0

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
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
    current_supply = day_context['supply']

    if my_status['hp'] <= 2: # Very critical HP, must get water
        bid = max(highest_prev_bid + 5.0, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4: # Low HP, need water
        bid = max(highest_prev_bid + 2.0, DAILY_SALARY * 0.85)
    else: # Healthy HP
        supply_range_size = MAX_SUPPLY - MIN_SUPPLY
        if supply_range_size == 0:
            normalized_supply = 0.5 # Default to middle if range is zero
        else:
            normalized_supply = (current_supply - MIN_SUPPLY) / supply_range_size
        
        min_healthy_bid_percentage = 0.60
        max_healthy_bid_percentage = 0.80
        
        # Bids are higher when supply is lower (normalized_supply closer to 0)
        bid_percentage = min_healthy_bid_percentage + (max_healthy_bid_percentage - min_healthy_bid_percentage) * (1.0 - normalized_supply)
        
        bid = max(highest_prev_bid + 0.5, DAILY_SALARY * bid_percentage)

    bid = min(bid, my_status['budget'])

    if bid <= 0 and my_status['budget'] > 0:
        bid = 1.0

    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    # If supply is less than my requirement, I cannot get water. Bid 0 to save budget.
    if day_context['supply'] < WATER_REQ:
        return 0.0

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no alive opponents, bid minimally to get water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid_amount = 0.0 # Initialize bid_amount

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # Determine how many agents can potentially get water
        num_possible_winners = int(day_context['supply'] // WATER_REQ)
        
        # Critical HP: Bid very high to survive
        if my_status['hp'] <= 3:
            bid_amount = max(DAILY_SALARY * 0.95, highest_prev_bid + 5)
        # Low HP: Bid high
        elif my_status['hp'] <= 5:
            bid_amount = max(DAILY_SALARY * 0.85, highest_prev_bid + 3)
        # Healthy HP: Be strategic
        else:
            if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents were very aggressive
                # If supply is scarce, still need to be competitive
                if num_possible_winners < len(alive_opponents) + 1: 
                    bid_amount = max(DAILY_SALARY * 0.7, highest_prev_bid + 1)
                else: # Enough for everyone, try to get it cheaper
                    bid_amount = max(DAILY_SALARY * 0.5, highest_prev_bid * 0.9)
            else: # Opponents were moderate or low
                if num_possible_winners > len(alive_opponents): # More slots than agents, bid low
                    bid_amount = DAILY_SALARY * 0.2
                elif num_possible_winners >= 1: # Competitive, bid slightly above
                    bid_amount = max(DAILY_SALARY * 0.4, highest_prev_bid + 1)
                else: # Fallback, should not happen if supply >= WATER_REQ
                    bid_amount = DAILY_SALARY * 0.1 
    else: # No previous bids available (e.g., Day 1, or all opponents were eliminated/didn't bid)
        if my_status['hp'] <= 3:
            bid_amount = DAILY_SALARY * 0.9
        elif my_status['hp'] <= 5:
            bid_amount = DAILY_SALARY * 0.7
        else:
            # First day or no bids, and healthy. Bid moderately.
            num_possible_winners = int(day_context['supply'] // WATER_REQ)
            if num_possible_winners > len(alive_opponents):
                 bid_amount = DAILY_SALARY * 0.2
            else:
                 bid_amount = DAILY_SALARY * 0.55

    final_bid = min(my_status['budget'], bid_amount)
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no alive opponents, bid minimally to save budget but still win water.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Look at yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Core bidding logic based on HP and opponent's previous bids
    bid = 0.0

    if my_status['hp'] <= 4: # Low HP, need water urgently
        # Bid aggressively to win. Try to outbid yesterday's highest by a good margin.
        base_bid = DAILY_SALARY * 0.95 # Start with a high base (142.5)
        if highest_prev_bid > 0:
            bid = max(base_bid, highest_prev_bid + 2.0) # Ensure beating yesterday's high
        else:
            bid = base_bid
    else: # Healthy HP
        # Try to win, but also save budget.
        if highest_prev_bid > DAILY_SALARY * 0.8: # Opponents are very aggressive
            bid = DAILY_SALARY * 0.9 # Be competitive (135)
            bid = max(bid, highest_prev_bid + 1.0)
        elif highest_prev_bid > DAILY_SALARY * 0.5: # Opponents are moderately aggressive
            bid = DAILY_SALARY * 0.8 # Be competitive (120)
            bid = max(bid, highest_prev_bid + 0.5)
        elif highest_prev_bid > 0: # Opponents bid low
            bid = DAILY_SALARY * 0.6 # Try to win cheaply (90)
            bid = max(bid, highest_prev_bid + 0.1)
        else: # No previous bids or all were 0 (e.g., Day 1 or broken opponents)
            bid = DAILY_SALARY * 0.7 # A reasonable starting bid (105)

    # If it's the last day and HP is critical, bid everything.
    if day_context['day'] == EPISODE_DAYS:
        if my_status['hp'] <= 2:
            bid = my_status['budget']
        else:
            # Still healthy on last day, can be slightly less aggressive but still aim to win.
            bid = min(my_status['budget'], DAILY_SALARY * 1.0)

    # Final checks
    bid = max(bid, 1.0) # Minimum bid to participate
    bid = min(bid, my_status['budget']) # Cannot bid more than current budget

    return bid
"""
