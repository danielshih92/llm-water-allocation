# ============================================================
# Experiment: exp_050
# Agent: Cindy
# Source: exp_050
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    my_water_requirement = 13
    my_daily_salary = 150

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Strategy 1: If I am the only one left
    if num_alive_opponents == 0:
        # Bid a minimal amount to secure water
        return min(my_budget, my_daily_salary * 0.1)

    # Gather opponent info from previous trace
    opponent_prev_bids = []
    opponent_hps = []
    opponent_budgets = []
    opponent_water_reqs = []

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            opponent_prev_bids.append(prev['bid'])
        opponent_hps.append(opp['hp'])
        opponent_budgets.append(opp['budget'])
        opponent_water_reqs.append(opp['water_requirement'])

    max_opponent_prev_bid = max(opponent_prev_bids) if opponent_prev_bids else 0

    # Calculate total demand
    total_opponent_water_req = sum(opponent_water_reqs)
    total_demand_all_agents = my_water_requirement + total_opponent_water_req

    bid = 0.0

    # Strategy 2: My HP is critically low
    if my_hp <= 2:
        bid = my_daily_salary * 0.95 # Bid very high to ensure survival
    # Strategy 3: Scarcity scenario (supply not enough for everyone)
    elif current_supply < total_demand_all_agents:
        # Need to outbid opponents, especially if they are also struggling
        if max_opponent_prev_bid > 0:
            bid = max_opponent_prev_bid + 5.0 # Bid slightly higher than the highest previous bid
            # If my HP is also low, be more aggressive
            if my_hp <= 4:
                bid = max(bid, my_daily_salary * 0.75)
        else: # No previous bids, assume a competitive bid
            bid = my_daily_salary * 0.6
    # Strategy 4: Abundance scenario (supply is enough for everyone)
    elif current_supply >= total_demand_all_agents:
        # No need to overbid, save budget
        if max_opponent_prev_bid > 0:
            # Try to bid slightly less than max previous bid if possible, but ensure getting water
            bid = max(my_daily_salary * 0.2, max_opponent_prev_bid * 0.8)
            if bid < 5.0: bid = 5.0 # Minimum bid
        else: # No previous bids, default low bid
            bid = my_daily_salary * 0.25
    # Strategy 5: Default / Balanced (if previous conditions don't fully capture)
    else:
        # A moderate bid if not in crisis or extreme scarcity/abundance
        if my_hp <= 4:
            bid = my_daily_salary * 0.7
        elif max_opponent_prev_bid > 0:
            bid = max_opponent_prev_bid + 1.0 # Slightly higher than previous
        else:
            bid = my_daily_salary * 0.5

    # Ensure bid does not exceed available budget and is positive
    final_bid = max(0.1, min(my_budget, bid))

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

    # If no opponents, bid minimum to save budget
    if not alive_opponents:
        return min(my_status['budget'], 1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid = 0

    # Desperate state: HP is very low (3 or less)
    if my_status['hp'] <= 3:
        bid = DAILY_SALARY * 0.98 # Bid very aggressively
    else: # Not desperate
        competitive_base = DAILY_SALARY * 0.5 # Default competitive bid
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            # Try to outbid the highest previous bid slightly, but ensure it's at least the competitive_base
            competitive_base = max(competitive_base, highest_prev_bid + 2)
        
        bid = competitive_base

        # Adjust based on supply and number of competitors
        # CRITICAL INDEX RULE: day_context['supply'] is float, use int() for floor division result
        num_slots = int(day_context['supply'] // WATER_REQ)

        if num_slots >= len(alive_opponents) + 1: # Enough water for everyone + me
            bid = min(bid, DAILY_SALARY * 0.15) # Bid very low to save money
        elif num_slots < 2: # Very tight supply, only 1 or 2 winners
            # Even if not desperate, tight supply means higher competition
            bid = max(bid, DAILY_SALARY * 0.75) # Bid higher to increase chances

        # Cap bid at daily salary if not desperate
        bid = min(bid, DAILY_SALARY)

    # Final adjustments
    # Ensure bid does not exceed current budget
    bid = min(bid, my_status['budget'])
    # Ensure bid is at least 1 (to participate)
    bid = max(bid, 1)
    
    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            else:
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else:
            bid_amount = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)
            return min(my_status['budget'], bid_amount)
    else:
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        else:
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

    remaining_days = EPISODE_DAYS - day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        # No opponents, bid minimum to secure water
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Default bid if no previous bids or as a baseline competitive level
    base_bid = DAILY_SALARY * 0.6 # Starting at 90

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Always try to outbid slightly if possible, especially since only one winner for my water_requirement
        base_bid = max(base_bid, highest_prev_bid + 1.0)

    bid = base_bid

    # Priority 1: Critical HP or already missed water
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        # Bid extremely high to survive
        bid = DAILY_SALARY * 0.98 # 147
    # Priority 2: Low HP
    elif my_status['hp'] <= 5:
        # Be very aggressive, ensure bid is high enough
        bid = max(bid, DAILY_SALARY * 0.85) # Min 127.5
    # Priority 3: End game push if not full HP
    elif remaining_days <= 2 and my_status['hp'] < 10:
        bid = max(bid, DAILY_SALARY * 0.9) # Min 135
    # Priority 4: Normal HP, competitive bidding (bid is already set by base_bid logic)
    
    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], bid)
    
    # Ensure bid is non-negative
    return max(0.0, final_bid)
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
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    strong_opponent_ids = ["Alex", "Eric"]
    
    yesterday_strong_bids = []
    for opp_id in strong_opponent_ids:
        if opp_id in opponents_status and opponents_status[opp_id]['alive']:
            opp = opponents_status[opp_id]
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_strong_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.8

    supply_factor = 1.0
    if day_context['supply'] <= 18:
        supply_factor = 1.15
    elif day_context['supply'] >= 22:
        supply_factor = 0.9
    
    current_bid = base_bid * supply_factor

    if yesterday_strong_bids:
        highest_strong_prev_bid = max(yesterday_strong_bids)
        if highest_strong_prev_bid >= DAILY_SALARY * 0.9:
            current_bid = max(current_bid, highest_strong_prev_bid + 5)
        elif highest_strong_prev_bid >= DAILY_SALARY * 0.7:
            current_bid = max(current_bid, highest_strong_prev_bid + 2)
        else:
            current_bid = min(current_bid, highest_strong_prev_bid + 10)

    if my_status['hp'] <= 3:
        current_bid = max(current_bid, DAILY_SALARY * 1.05)
    elif my_status['hp'] <= 5:
        current_bid = max(current_bid, DAILY_SALARY * 0.95)
    
    final_bid = min(my_status['budget'], current_bid)

    if my_status['hp'] <= 1:
        final_bid = max(final_bid, DAILY_SALARY * 0.9)
    elif day_context['day'] > EPISODE_DAYS - 3:
        final_bid = max(final_bid, DAILY_SALARY * 0.9)

    final_bid = max(1.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no active opponents, bid low to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Decision logic based on yesterday's highest pressure
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents are bidding very aggressively
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # If my HP is good, I can risk bidding lower to save money
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            else: # If my HP is low, I need water, so bid high
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        # Normal or moderate pressure, bid slightly above previous high to secure water
        else:
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))

    # If no previous bids (e.g., Day 1 or all opponents were dead yesterday)
    if my_status['hp'] <= 2: # If my HP is low, bid high to survive
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    else: # Otherwise, bid moderately
        return min(my_status['budget'], DAILY_SALARY * 0.55)
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

    # Base bid if no specific conditions apply
    base_bid = DAILY_SALARY * 0.7 # Moderate bid

    # If no opponents, bid conservatively
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Get yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.85
    
    # Adjust bid based on yesterday's highest bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If yesterday's highest bid was very high, we need to compete
        if highest_prev_bid >= DAILY_SALARY * 0.8: # High competition
            base_bid = max(base_bid, highest_prev_bid + 5) # Try to slightly outbid
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # Moderate competition
            base_bid = max(base_bid, highest_prev_bid + 2)
        else: # Low competition, don't overbid
            base_bid = min(base_bid, DAILY_SALARY * 0.6) # Cap bid if others were low
    
    # Adjust bid based on supply scarcity
    # Estimate total water requirement for all alive players
    estimated_total_water_req = WATER_REQ # My requirement
    for opp in alive_opponents:
        estimated_total_water_req += opp['water_requirement'] # Add opponent requirements

    if day_context['supply'] < estimated_total_water_req:
        # Supply is scarce, increase bid aggressiveness
        base_bid *= 1.15 # Increase by 15%
    elif day_context['supply'] >= estimated_total_water_req * 1.5:
        # Supply is abundant, can afford to be less aggressive
        base_bid *= 0.9 # Decrease by 10%

    # Ensure the bid does not exceed available budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure a minimum bid if budget allows, to at least participate
    if my_status['budget'] > 0 and final_bid <= 0:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.1) # Bid a small fraction of salary

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

    days_remaining = EPISODE_DAYS - day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Default bid - a balanced approach
    bid_amount = DAILY_SALARY * 0.6

    # Analyze yesterday's bids to gauge competition
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # --- Bidding logic based on my status and opponent's previous actions ---

    # Priority 1: Critical HP - Bid max to survive
    if my_status['hp'] <= WATER_REQ * 0.5: # HP <= 6.5
        bid_amount = DAILY_SALARY * 1.0
        if highest_prev_bid > 0:
            bid_amount = max(bid_amount, highest_prev_bid + 1) # Ensure we try to outbid

    # Priority 2: Low HP or missed water - Bid aggressively
    elif my_status['hp'] <= WATER_REQ or my_status['no_water_days'] > 0: # HP <= 13
        bid_amount = DAILY_SALARY * 0.9
        if highest_prev_bid > 0:
            bid_amount = max(bid_amount, highest_prev_bid + 5) # Try to outbid significantly

    # Priority 3: End game approaching and not super safe
    elif days_remaining <= 2 and my_status['hp'] < EPISODE_DAYS * WATER_REQ * 0.7: # HP < 91
        bid_amount = DAILY_SALARY * 0.95
        if highest_prev_bid > 0:
            bid_amount = max(bid_amount, highest_prev_bid + 5)

    # Priority 4: Moderate/Good HP - Adapt to opponent's aggression
    else:
        if highest_prev_bid > DAILY_SALARY * 0.8: # Opponents were very aggressive
            # If my HP is very good, I can afford to save budget
            if my_status['hp'] > WATER_REQ * 2: # Very good HP (> 26)
                bid_amount = DAILY_SALARY * 0.6 # Save budget
            else: # Good HP, but not super high, still compete strongly
                bid_amount = DAILY_SALARY * 0.75
        elif highest_prev_bid > DAILY_SALARY * 0.5: # Moderate competition
            bid_amount = highest_prev_bid + 1 # Try to win by slightly outbidding
        else: # Low competition or no significant previous bids
            bid_amount = DAILY_SALARY * 0.5 # A bit lower to save budget

    # If no opponents, bid minimally to save budget
    if num_alive_opponents == 0:
        bid_amount = DAILY_SALARY * 0.3

    # Final bid adjustments
    final_bid = min(my_status['budget'], bid_amount)

    # Ensure a minimum bid if budget allows, to stay in the game
    if final_bid < DAILY_SALARY * 0.1 and my_status['budget'] >= DAILY_SALARY * 0.1:
        final_bid = DAILY_SALARY * 0.1
    elif final_bid < 1.0 and my_status['budget'] >= 1.0:
        final_bid = 1.0

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

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_budget, MY_DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid_amount = MY_DAILY_SALARY * 0.55

    if my_hp <= 2 or my_no_water_days >= 1:
        bid_amount = MY_DAILY_SALARY * 0.98
    elif current_day >= EPISODE_DAYS - 2:
        bid_amount = MY_DAILY_SALARY * 0.9
    elif my_hp <= 4:
        bid_amount = MY_DAILY_SALARY * 0.8

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= MY_DAILY_SALARY * 0.85:
            if my_hp <= 3 or my_no_water_days >= 1:
                bid_amount = max(bid_amount, highest_prev_bid + 5)
            else:
                bid_amount = max(bid_amount, highest_prev_bid + 1)
        elif highest_prev_bid >= MY_DAILY_SALARY * 0.5:
            if my_hp <= 4:
                bid_amount = max(bid_amount, highest_prev_bid + 2)
            else:
                bid_amount = max(bid_amount, highest_prev_bid + 1)
        else:
            if my_hp > 5 and my_budget > MY_DAILY_SALARY * 2:
                bid_amount = min(bid_amount, highest_prev_bid + 1)
            else:
                bid_amount = max(bid_amount, highest_prev_bid + 1)

    if num_alive_opponents >= 1 and current_supply < MY_WATER_REQ * 2:
        if my_hp <= 3 or my_no_water_days >= 1:
            bid_amount = max(bid_amount, MY_DAILY_SALARY * 0.99)
        elif yesterday_bids:
            bid_amount = max(bid_amount, max(yesterday_bids) + 10)

    final_bid = min(my_budget, max(1.0, bid_amount))

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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    highest_prev_bid = 0.0
    num_bidding_opponents = 0
    num_desperate_opponents = 0

    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            bid = prev_trace['bid']
            highest_prev_bid = max(highest_prev_bid, bid)
            num_bidding_opponents += 1
            
            opp_hp_after_prev_day = prev_trace.get('hp_after', opp['hp'])
            if opp_hp_after_prev_day <= opp['water_requirement'] * 1.5:
                num_desperate_opponents += 1

    my_desperation_factor = 1.0
    if my_hp <= WATER_REQ * 1.0:
        my_desperation_factor = 1.5
    if my_hp <= WATER_REQ * 0.5:
        my_desperation_factor = 2.5
    if my_status['no_water_days'] > 0:
        my_desperation_factor *= (1 + my_status['no_water_days'] * 0.7)

    num_water_slots = int(current_supply // WATER_REQ)

    base_bid = DAILY_SALARY * 0.6 * my_desperation_factor

    if highest_prev_bid > 0:
        if num_water_slots <= len(alive_opponents):
            base_bid = max(base_bid, highest_prev_bid * 1.1)
        else:
            base_bid = max(base_bid, highest_prev_bid * 1.05)

    if num_desperate_opponents >= num_water_slots and num_water_slots < len(alive_opponents) + 1:
        base_bid = max(base_bid, DAILY_SALARY * 1.0 * my_desperation_factor)

    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 3:
        base_bid *= 1.2
    elif current_day <= 2:
        base_bid *= 0.9

    final_bid = min(my_budget, base_bid)

    if my_hp <= WATER_REQ * 1.5 and my_budget > 0 and final_bid < DAILY_SALARY * 0.4:
        final_bid = min(my_budget, DAILY_SALARY * 0.4 * my_desperation_factor)
    
    if my_hp <= WATER_REQ * 0.5 and my_budget > 0:
        final_bid = min(my_budget, my_budget * 0.98)

    if my_budget > 0 and final_bid < 1.0:
        final_bid = min(my_budget, 1.0)

    return max(1.0, final_bid)
"""
