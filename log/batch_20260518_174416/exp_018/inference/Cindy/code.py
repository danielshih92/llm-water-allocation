# ============================================================
# Experiment: exp_018
# Agent: Cindy
# Source: exp_018
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

    # If no opponents, bid minimally to get water
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # --- Determine base bid based on my HP and no_water_days ---
    # Default moderate bid
    base_bid = DAILY_SALARY * 0.5 

    if my_status['hp'] <= 2: # Critical HP, need water at almost any cost
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 3: # Low HP, need water
        base_bid = DAILY_SALARY * 0.8
    elif my_status['no_water_days'] > 0: # Losing HP, need water
        base_bid = DAILY_SALARY * 0.7
    # else comfortable, base_bid remains 0.5 * DAILY_SALARY

    # --- Adjust bid based on supply and demand ---
    total_water_needed_by_all = WATER_REQ
    for opp in alive_opponents:
        total_water_needed_by_all += opp['water_requirement']

    current_supply = day_context['supply']

    is_supply_scarce = current_supply < total_water_needed_by_all
    is_supply_abundant = current_supply >= total_water_needed_by_all + WATER_REQ # Enough for everyone + me again

    if is_supply_abundant:
        # Very abundant water, can afford to bid lower, especially if healthy
        if my_status['hp'] > 3:
            base_bid = min(base_bid, DAILY_SALARY * 0.35)
        else: # Still abundant, but I'm not super healthy, so bid a bit more to be safe
            base_bid = min(base_bid, DAILY_SALARY * 0.5)
    elif is_supply_scarce:
        # Scarce water, competition will be higher. Increase bid if not already high.
        if my_status['hp'] > 2: # Not critical, but need to be competitive
            base_bid = max(base_bid, DAILY_SALARY * 0.7)
        # If critical (hp <= 2), base_bid is already high, no further increase needed just for scarcity here.

    # --- Adjust bid based on opponent's previous bids (game theory) ---
    yesterday_opp_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_opp_bids.append(prev['bid'])

    max_prev_opp_bid = 0.0
    if yesterday_opp_bids:
        max_prev_opp_bid = max(yesterday_opp_bids)

    # If opponents bid very high yesterday
    if max_prev_opp_bid >= DAILY_SALARY * 0.85:
        if is_supply_scarce and my_status['hp'] > 3: # Healthy and supply is tight, let them fight
            final_bid = min(base_bid, DAILY_SALARY * 0.3)
        else:
            # Either supply is not scarce, or I'm not healthy. Must compete.
            final_bid = max(base_bid, max_prev_opp_bid + 2.0) # Outbid them slightly
    elif max_prev_opp_bid > 0: # Opponents made some bid yesterday (not extremely high)
        # Increment slightly above their max bid to be competitive, but not too aggressive
        final_bid = max(base_bid, max_prev_opp_bid + 1.0)
    else: # No significant previous bids or all were 0
        final_bid = base_bid # Use the base bid determined by my status and supply

    # --- Final bid constraints ---
    final_bid = max(0.0, final_bid) # Ensure bid is not negative
    final_bid = min(final_bid, float(my_status['budget'])) # Cannot bid more than budget

    # Safeguard: if I desperately need water and have budget, but bid became 0, ensure a minimal bid
    if final_bid == 0 and my_status['budget'] > 0 and my_status['hp'] <= 3:
        final_bid = min(float(my_status['budget']), DAILY_SALARY * 0.1)

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
    current_day = day_context['day']
    supply = day_context['supply']

    CRITICAL_HP = 2 
    LOW_HP = 4      
    MEDIUM_HP = 7   

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    target_bid = 0.0

    if my_hp <= CRITICAL_HP:
        target_bid = DAILY_SALARY * 0.95
    elif my_hp <= LOW_HP:
        target_bid = DAILY_SALARY * 0.85
    elif my_hp <= MEDIUM_HP:
        target_bid = DAILY_SALARY * 0.7
    else:
        target_bid = DAILY_SALARY * 0.6

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if my_hp <= LOW_HP:
            target_bid = max(target_bid, highest_prev_bid + 2.5)
        else:
            target_bid = max(target_bid, highest_prev_bid + 1.0)
            
    if current_day >= EPISODE_DAYS - 2:
        if my_hp <= LOW_HP:
            target_bid = max(target_bid, DAILY_SALARY * 0.98)
        else:
            target_bid = max(target_bid, DAILY_SALARY * 0.9)
    elif current_day >= EPISODE_DAYS - 4:
        if my_hp <= MEDIUM_HP:
            target_bid = max(target_bid, DAILY_SALARY * 0.8)

    final_bid = min(my_budget, target_bid)
    
    if my_hp <= CRITICAL_HP and my_budget < target_bid:
        final_bid = my_budget

    if final_bid < 1.0 and my_budget > 0:
        final_bid = 1.0
    
    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to save budget.
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # Base bid: Start aggressive due to single water slot
    base_bid = DAILY_SALARY * 0.8 # Default aggressive bid: 120.0

    # Survival mode: If HP is very low or I missed water yesterday
    if my_hp <= 2 or my_no_water_days >= 1:
        base_bid = DAILY_SALARY * 0.95 # Very aggressive bid: 142.5
    elif my_hp <= 4: # Medium low HP
        base_bid = DAILY_SALARY * 0.9 # Aggressive bid: 135.0

    # Adjust bid based on opponent's previous highest bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents bid very high, I need to exceed that, especially in survival mode
        if highest_prev_bid >= DAILY_SALARY * 0.75: # e.g., 112.5
            # Try to outbid by a small margin
            base_bid = max(base_bid, highest_prev_bid + 2.0)

    # Final bid must be within budget
    final_bid = min(my_budget, base_bid)

    return final_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    # In this scenario (supply 15-25, water_req 13), only one player can get their full water requirement.
    # int(15/13) = 1, int(25/13) = 1
    num_water_slots = int(day_context['supply'] / WATER_REQ)

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimum to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Determine the highest daily salary among competitors to gauge bidding pressure
    max_competitor_salary = 0
    for opp in alive_opponents:
        if opp['daily_salary'] > max_competitor_salary:
            max_competitor_salary = opp['daily_salary']
            
    # Desperation bids based on how many days without water
    if my_status['no_water_days'] == 2: # Critical: I die if I don't get water today
        return my_status['budget'] # Bid everything to survive
    elif my_status['no_water_days'] == 1: # High risk: I die tomorrow if I don't get water today
        # Bid very aggressively, ensuring I outbid the strongest competitor or a solid amount above my salary
        aggressive_bid = max(max_competitor_salary + 5, DAILY_SALARY * 1.1)
        return min(my_status['budget'], aggressive_bid)

    # Normal bidding strategy: Aim to outbid the strongest competitor or at least my own salary to secure water
    target_bid = DAILY_SALARY + 2 # A small margin above my salary to win ties

    # If a competitor has a higher salary, I must try to match/exceed it to win consistently
    if max_competitor_salary > DAILY_SALARY:
        target_bid = max_competitor_salary + 2 # Slightly above the highest competitor's salary

    # Ensure the bid does not exceed current budget
    final_bid = min(my_status['budget'], target_bid)

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MY_HP = my_status['hp']
    MY_BUDGET = my_status['budget']
    SUPPLY = day_context['supply']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(MY_BUDGET, WATER_REQ * 1.05)

    yesterday_bids = []
    total_water_needed_by_opponents = 0
    for opp in alive_opponents:
        total_water_needed_by_opponents += opp['water_requirement']
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    total_water_needed_including_me = WATER_REQ + total_water_needed_by_opponents

    bid = WATER_REQ * 1.05 

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if SUPPLY < total_water_needed_including_me:
            if MY_HP <= 3:
                bid = max(bid, highest_prev_bid + 5, DAILY_SALARY * 0.9)
            else:
                bid = max(bid, highest_prev_bid + 2)
        else:
            if highest_prev_bid > bid:
                bid = max(bid, highest_prev_bid + 1)
            if MY_HP <= 2:
                bid = max(bid, DAILY_SALARY * 0.8)

    if MY_HP <= 1:
        bid = DAILY_SALARY * 0.99
    elif my_status['no_water_days'] > 0:
        bid = max(bid, DAILY_SALARY * 0.85)

    bid = min(bid, MY_BUDGET)
    bid = max(1.0, bid)

    if MY_HP > 1:
        bid = min(bid, DAILY_SALARY)

    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQUIREMENT = 13
    MY_DAILY_SALARY = 150
    EPISODE_DAYS = 10

    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        return min(my_status['budget'], MY_DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid_factor = 0.55

    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        base_bid_factor = 0.95
    elif my_status['hp'] >= 8:
        base_bid_factor = 0.45
    
    effective_participants = num_alive_opponents + 1
    if effective_participants > 0:
        supply_per_participant = current_supply / effective_participants
        
        if supply_per_participant < MY_WATER_REQUIREMENT * 0.8:
            base_bid_factor += 0.20
        elif supply_per_participant < MY_WATER_REQUIREMENT * 1.2:
            base_bid_factor += 0.05
        elif supply_per_participant > MY_WATER_REQUIREMENT * 1.5:
            base_bid_factor -= 0.10

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)

        if max_yesterday_bid >= MY_DAILY_SALARY * 0.8:
            base_bid_factor = max(base_bid_factor, (max_yesterday_bid + 5) / MY_DAILY_SALARY)
        elif max_yesterday_bid >= MY_DAILY_SALARY * 0.6:
            base_bid_factor = max(base_bid_factor, (avg_yesterday_bid + 2) / MY_DAILY_SALARY)
        else:
            if my_status['hp'] > 3:
                base_bid_factor = min(base_bid_factor, (avg_yesterday_bid + 1) / MY_DAILY_SALARY)

    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 3:
        if my_status['hp'] <= 3:
             base_bid_factor = max(base_bid_factor, 0.98)
        else:
            base_bid_factor = max(base_bid_factor, 0.75)

    final_bid = MY_DAILY_SALARY * base_bid_factor

    final_bid = min(my_status['budget'], final_bid)

    if final_bid <= 0 and my_status['budget'] > 0:
        return 1.0
    elif my_status['budget'] <= 0:
        return 0.0

    if final_bid < 1.0 and my_status['budget'] >= 1.0:
        return 1.0

    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    bid = 0.0

    # Survival mode: If HP is critically low, bid very aggressively
    if my_status['hp'] <= 2:
        bid = DAILY_SALARY * 0.95 # Almost full salary to guarantee water
    else:
        # Normal competition mode
        yesterday_bids = []
        for opp in alive_opponents:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)

            # High competition detected (e.g., David's aggressive bids)
            if highest_prev_bid >= DAILY_SALARY * 0.8: # e.g., >= 120
                bid = DAILY_SALARY * 0.85 # Bid very high, but leave some budget
            # Moderate competition
            elif highest_prev_bid >= DAILY_SALARY * 0.5: # e.g., >= 75
                bid = highest_prev_bid * 1.05 + 5 # Bid slightly above, with a buffer
                bid = min(bid, DAILY_SALARY * 0.8) # Cap bid to prevent overspending in moderate scenarios
            # Low competition
            else: # highest_prev_bid < DAILY_SALARY * 0.5 (75)
                bid = max(DAILY_SALARY * 0.55, highest_prev_bid + 5) # Ensure a decent minimum bid (82.5) or slightly above low bids
        else:
            # No yesterday bids from alive opponents, or first day
            bid = DAILY_SALARY * 0.6 # A solid default bid (90)

    # Ensure bid does not exceed current budget and is at least 1
    final_bid = max(1.0, min(my_status['budget'], bid))
\    return final_bid
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
    num_alive_competitors = len(alive_opponents)

    # Base bid: Moderate starting point
    bid_amount = DAILY_SALARY * 0.5

    # Survival mode: If HP is critical or water was missed yesterday
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        bid_amount = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        bid_amount = DAILY_SALARY * 0.8

    # Abundant water check: Adjust bid if supply is sufficient for everyone
    # CRITICAL INDEX RULE: day_context['supply'] is float, ensure int() for logical comparison if needed, but not for direct indexing here.
    if day_context['supply'] >= WATER_REQ * (num_alive_competitors + 1):
        # Water is abundant, can bid lower to save budget if relatively healthy
        if my_status['hp'] >= 8:
            bid_amount = min(bid_amount, DAILY_SALARY * 0.3)
        else:
            bid_amount = min(bid_amount, DAILY_SALARY * 0.5)
    # If supply is very scarce (less than 1 unit per person on average)
    elif day_context['supply'] < WATER_REQ * (num_alive_competitors + 1) / 2:
        if my_status['hp'] <= 5: # Only be aggressive if needed
            bid_amount = max(bid_amount, DAILY_SALARY * 0.75)

    # Opponent reaction based on yesterday's bids (previous_trace)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If highest bid was very high, it signals strong competition
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] <= 3: # Critical, must compete aggressively
                bid_amount = max(bid_amount, highest_prev_bid + 5.0)
            else: # Healthy, try to outbid smartly or conserve
                bid_amount = max(bid_amount, average_prev_bid * 1.05)
        # If highest bid was moderate, slightly exceed it to secure water
        elif highest_prev_bid > DAILY_SALARY * 0.4:
            bid_amount = max(bid_amount, highest_prev_bid + 1.0)
        # If highest bid was low, ensure we get water but still conserve
        else:
            bid_amount = max(bid_amount, highest_prev_bid * 1.1)

    # Ensure bid is within budget and non-negative
    final_bid = min(bid_amount, my_status['budget'])
    final_bid = max(0.0, final_bid) # Ensure bid is not negative

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    base_bid = DAILY_SALARY * 0.7
    
    competition_factor = 1 + (num_alive_opponents * 0.05)
    current_bid = base_bid * competition_factor

    available_water_units = int(day_context['supply'] // WATER_REQ)
    if available_water_units <= num_alive_opponents:
        current_bid += DAILY_SALARY * 0.15
    elif available_water_units > num_alive_opponents + 1:
        current_bid -= DAILY_SALARY * 0.1

    if my_status['hp'] <= 2:
        current_bid = max(current_bid, DAILY_SALARY * 0.95)
    elif my_status['hp'] == 3:
        current_bid = max(current_bid, DAILY_SALARY * 0.85)

    if day_context['day'] >= EPISODE_DAYS - 2 and my_status['budget'] > DAILY_SALARY * 2:
        current_bid += DAILY_SALARY * 0.1

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        if max_yesterday_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                current_bid = min(current_bid, DAILY_SALARY * 0.6)
            else:
                current_bid = max(current_bid, max_yesterday_bid + 5)
        elif max_yesterday_bid >= DAILY_SALARY * 0.6:
            current_bid = max(current_bid, max_yesterday_bid + 5)
        else:
            current_bid = max(current_bid, DAILY_SALARY * 0.7)

    final_bid = min(my_status['budget'], current_bid)
    final_bid = max(1, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to secure water.
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # Determine base bid
    base_bid = DAILY_SALARY * 0.6 # A moderate bid

    # Adjust bid based on my HP
    remaining_days = EPISODE_DAYS - current_day
    if my_hp <= 2: # Critical HP, need water urgently
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.8
    elif my_hp >= remaining_days + 1: # High HP, can afford to save a bit
        base_bid = DAILY_SALARY * 0.55

    # Adjust bid based on opponent's highest bid from yesterday
    if yesterday_bids:
        max_opp_bid_yesterday = max(yesterday_bids)
        # If max opponent bid was high, we need to be competitive
        if max_opp_bid_yesterday >= DAILY_SALARY * 0.8:
            if my_hp <= 2: # If critical, bid more aggressively
                base_bid = max(base_bid, max_opp_bid_yesterday + 5.0)
            else:
                base_bid = max(base_bid, max_opp_bid_yesterday + 1.0)
        elif max_opp_bid_yesterday < DAILY_SALARY * 0.5:
            # If opponents bid low, we can try to save money, but still secure water
            base_bid = min(base_bid, max_opp_bid_yesterday + 10.0)

    # Adjust bid based on remaining days and budget
    if remaining_days > 0:
        # If budget is getting tight, try to conserve if HP allows
        if my_budget < remaining_days * (DAILY_SALARY * 0.6):
            if my_hp > 3: # If not critical, try to save
                base_bid = min(base_bid, DAILY_SALARY * 0.5)
            else: # If critical, still need to bid high
                base_bid = max(base_bid, DAILY_SALARY * 0.9)

    # Final bid cannot exceed current budget
    final_bid = min(my_budget, base_bid)

    # Ensure bid is at least 0.0 (cannot be negative)
    final_bid = max(final_bid, 0.0)

    return final_bid
"""
