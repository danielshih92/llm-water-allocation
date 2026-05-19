# ============================================================
# Experiment: exp_030
# Agent: Cindy
# Source: exp_030
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    # Ensure bid doesn't exceed budget
    max_affordable_bid = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        return min(max_affordable_bid, DAILY_SALARY * 0.1)

    # Base bid strategy based on HP and general market conditions
    base_bid = DAILY_SALARY * 0.5 # Default moderate bid

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP: 2 days or less without water
        base_bid = DAILY_SALARY * 0.95 # Bid very aggressively
    elif my_status['hp'] <= 4: # Low HP: 3-4 days without water
        base_bid = DAILY_SALARY * 0.75 # Bid aggressively
    else: # Healthy HP
        # Consider supply and competition when healthy
        current_supply = day_context['supply']
        # Estimate total water demand if everyone wants water (including myself)
        total_potential_demand = WATER_REQ + sum(o['water_requirement'] for o in alive_opponents)

        if current_supply < total_potential_demand: # Supply is scarce relative to potential demand
            base_bid = DAILY_SALARY * 0.65 # Increase bid due to scarcity
        else: # Supply is abundant
            base_bid = DAILY_SALARY * 0.4 # Decrease bid due to abundance

    # Look at yesterday's situation (Trace) if available
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents bid very high yesterday, we might need to react
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents were aggressive
            if my_status['hp'] <= 2:
                base_bid = max(base_bid, highest_prev_bid + 1) # Must win, slightly over their max
            elif my_status['hp'] <= 4:
                base_bid = max(base_bid, highest_prev_bid * 0.9) # Try to get it, but don't overpay too much
            else:
                base_bid = min(base_bid, highest_prev_bid * 0.7) # Let them fight, save money if healthy
        elif highest_prev_bid <= DAILY_SALARY * 0.3: # Opponents were conservative
            base_bid = min(base_bid, highest_prev_bid + 5) # Try to get it cheaper, but slightly higher than them to win

        # Ensure my bid is competitive if I need water, based on yesterday's highest
        if my_status['hp'] <= 4: # If I need water, ensure my bid is competitive
            base_bid = max(base_bid, highest_prev_bid * 0.8) # At least 80% of their max bid, to stay in contention
        else:
            # If healthy, can be more conservative, but still consider yesterday's market
            base_bid = max(base_bid, highest_prev_bid * 0.5)

    # Final bid must be positive and within budget
    final_bid = max(1.0, min(base_bid, max_affordable_bid))

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
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    bid = DAILY_SALARY * 0.5

    if my_status['hp'] <= 2:
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5:
        bid = DAILY_SALARY * 0.8
    elif my_status['no_water_days'] > 0:
        bid = DAILY_SALARY * 0.7

    estimated_total_water_needed = WATER_REQ + sum([o['water_requirement'] for o in alive_opponents])
    
    if day_context['supply'] < estimated_total_water_needed:
        bid = max(bid, DAILY_SALARY * 0.75)
    
    if day_context['supply'] < WATER_REQ * 1.5:
        bid = max(bid, DAILY_SALARY * 0.85)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        if max_yesterday_bid >= DAILY_SALARY * 0.7:
            bid = max(bid, max_yesterday_bid + 5)
        elif max_yesterday_bid > bid:
            bid = max(bid, max_yesterday_bid + 1)
    
    remaining_days = EPISODE_DAYS - int(day_context['day'])
    if remaining_days <= 3 and my_status['hp'] < 10:
        bid = max(bid, DAILY_SALARY * 0.9)
    if remaining_days <= 1 and my_status['hp'] <= 2:
        bid = DAILY_SALARY * 0.99

    bid = max(1.0, bid)

    final_bid = min(bid, my_status['budget'])
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)
    
    high_bidders_yesterday = []
    low_bidders_yesterday = []
    
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev_trace = opp.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                opp_bid = prev_trace['bid']
                opp_salary = opp['daily_salary']
                
                if opp_bid > opp_salary * 0.7:
                    high_bidders_yesterday.append(opp_id)
                elif opp_bid > 0 and opp_bid < opp_salary * 0.5:
                    low_bidders_yesterday.append(opp_id)
    
    current_supply = day_context['supply']
    current_day = day_context['day']
    
    total_water_needed = WATER_REQ
    for opp in alive_opponents:
        total_water_needed += opp['water_requirement']

    num_full_req_met = int(current_supply // WATER_REQ)
    
    bid = DAILY_SALARY * 0.5
    
    if my_status['hp'] <= 3:
        bid = DAILY_SALARY * 0.95
    elif my_status['no_water_days'] >= 1:
        bid = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 5:
        bid = DAILY_SALARY * 0.8
    
    num_active_players = len(alive_opponents) + 1
    
    if current_supply < total_water_needed:
        if 'Alex' in high_bidders_yesterday:
            alex_prev_bid = opponents_status['Alex']['previous_trace']['bid']
            if num_full_req_met <= 2:
                bid = max(bid, alex_prev_bid + 5)
            else:
                bid = max(bid, DAILY_SALARY * 0.7)
        elif num_active_players > num_full_req_met:
            bid = max(bid, DAILY_SALARY * 0.65)
    
    elif current_supply >= total_water_needed:
        if 'Alex' in high_bidders_yesterday:
            alex_prev_bid = opponents_status['Alex']['previous_trace']['bid']
            if my_status['hp'] > 5:
                bid = min(bid, max(DAILY_SALARY * 0.4, alex_prev_bid * 0.9))
            else:
                bid = max(bid, DAILY_SALARY * 0.55)
        
        if 'Eric' in low_bidders_yesterday:
            bid = min(bid, DAILY_SALARY * 0.4)
        
        bid = min(bid, DAILY_SALARY * 0.5)

    remaining_days = 10 - current_day
    if remaining_days <= 2 and my_status['hp'] <= 5:
        bid = max(bid, DAILY_SALARY * 0.99)
    elif remaining_days <= 2 and my_status['budget'] > DAILY_SALARY * 5:
        bid = max(bid, DAILY_SALARY * 0.7)

    bid = min(bid, my_status['budget'])
    bid = max(1.0, bid)
    bid = round(bid, 2)
    
    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    VALUE_PER_UNIT = DAILY_SALARY / WATER_REQ

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return int(min(my_status['budget'], WATER_REQ * VALUE_PER_UNIT * 0.5))

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace')
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0.0

    bid = 0.0

    # Priority 1: Survival Mode - If HP is critically low or I've missed water previously
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        bid = DAILY_SALARY * 1.2
        if max_yesterday_bid > 0:
            bid = max(bid, max_yesterday_bid + VALUE_PER_UNIT * 2)
        bid = max(bid, DAILY_SALARY * 0.9)
    else:
        supply = day_context['supply']
        num_potential_winners = len(alive_opponents) + 1

        total_water_needed_by_all = num_potential_winners * WATER_REQ

        if supply >= total_water_needed_by_all * 1.2:
            bid = DAILY_SALARY * 0.6
            if max_yesterday_bid > 0:
                bid = max(bid, max_yesterday_bid * 0.9)
            bid = min(bid, DAILY_SALARY * 0.75)
        elif supply < total_water_needed_by_all * 0.8:
            bid = DAILY_SALARY * 1.0
            if max_yesterday_bid > 0:
                bid = max(bid, max_yesterday_bid + VALUE_PER_UNIT * 1.5)
            bid = min(bid, DAILY_SALARY * 1.3)
        else:
            bid = DAILY_SALARY * 0.8
            if max_yesterday_bid > 0:
                bid = max(bid, max_yesterday_bid + VALUE_PER_UNIT * 0.5)
            bid = min(bid, DAILY_SALARY * 1.1)

    bid = min(bid, my_status['budget'])
    bid = max(bid, WATER_REQ * VALUE_PER_UNIT * 0.1)
    bid = max(bid, 1.0)

    return int(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state, fixed for this challenge

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # --- Bid calculation logic ---
    base_bid = DAILY_SALARY * 0.5 # A moderate starting bid

    # Adjust bid based on my HP
    if my_hp <= 3: # Critical HP, bid very aggressively
        base_bid = DAILY_SALARY * 0.9
    elif my_hp <= 5: # Low HP, bid aggressively
        base_bid = DAILY_SALARY * 0.75
    elif my_status['no_water_days'] > 0: # If I missed water yesterday
        base_bid = DAILY_SALARY * 0.8

    # Adjust bid based on supply scarcity
    # Calculate how many agents can meet their water requirement
    potential_winners = int(current_supply / WATER_REQ)

    if potential_winners <= num_alive_opponents: # Supply is scarce relative to demand
        base_bid *= 1.2 # Increase bid due to scarcity
    elif potential_winners >= num_alive_opponents + 2: # Supply is abundant
        base_bid *= 0.8 # Decrease bid due to abundance
    
    # Adjust bid based on opponent's previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        min_prev_bid = min(yesterday_bids)

        # If opponents bid very high yesterday, I need to react
        if max_prev_bid >= DAILY_SALARY * 0.7:
            base_bid = max(base_bid, max_prev_bid * 1.05) # Try to slightly outbid high bidders
        # If opponents bid very low yesterday and supply was good, I can try to save
        elif min_prev_bid <= DAILY_SALARY * 0.3 and potential_winners > num_alive_opponents:
            base_bid = min(base_bid, min_prev_bid * 0.9) # Try to bid lower if possible

    # Final bid should not exceed budget
    final_bid = min(my_budget, base_bid)

    # Ensure bid is at least a minimum to be competitive
    min_competitive_bid = DAILY_SALARY * 0.15
    final_bid = max(final_bid, min_competitive_bid)

    # Strategic adjustment for end game
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_hp < 10: # Near end and HP is not full
        final_bid = min(my_budget, DAILY_SALARY * 0.95) # Bid very high to survive last days

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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_supply = day_context['supply']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    david_alive = False
    david_prev_bid = 0.0
    for opp_id, opp_data in opponents_status.items():
        if opp_id == "David" and opp_data['alive']:
            david_alive = True
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                david_prev_bid = prev_trace['bid']
            break

    bid_value = DAILY_SALARY * 0.65

    if my_hp <= 2:
        bid_value = DAILY_SALARY * 0.98
    elif my_hp <= 5:
        bid_value = DAILY_SALARY * 0.85
    elif my_hp > 7 and current_day > EPISODE_DAYS / 2:
        bid_value = DAILY_SALARY * 0.55

    if current_supply <= WATER_REQ + 2:
        bid_value = max(bid_value, DAILY_SALARY * 0.9)
    elif current_supply <= WATER_REQ + 5:
        bid_value = max(bid_value, DAILY_SALARY * 0.8)
    elif current_supply >= WATER_REQ + 10:
        bid_value = min(bid_value, DAILY_SALARY * 0.5)

    if david_alive and david_prev_bid > 0:
        if my_hp <= 5:
            bid_value = max(bid_value, david_prev_bid + 15)
        elif my_hp <= 7:
            bid_value = max(bid_value, david_prev_bid + 8)
        else:
            bid_value = max(bid_value, david_prev_bid + 3)
    else:
        other_yesterday_bids = []
        for opp in alive_opponents:
            prev_trace = opp.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                other_yesterday_bids.append(prev_trace['bid'])
        
        if other_yesterday_bids:
            highest_other_bid = max(other_yesterday_bids)
            if my_hp <= 5:
                bid_value = max(bid_value, highest_other_bid + 5)
            else:
                bid_value = max(bid_value, highest_other_bid + 2)

    final_bid = max(0.0, min(bid_value, my_budget))

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

    # Initialize bid based on a reasonable value for water
    # My 'value' for 13 units of water is my daily salary, 150, as losing water means losing 1 HP.
    bid = DAILY_SALARY * 0.7  # Default bid: 105

    # Adjust bid based on my current HP
    if my_status['hp'] <= 2:  # Critical HP, must get water
        bid = DAILY_SALARY * 0.98  # Bid very high (147)
    elif my_status['hp'] == 3:  # Low HP, need water
        bid = DAILY_SALARY * 0.90  # Bid high (135)
    elif my_status['hp'] >= 8:  # Comfortable HP, can be more conservative
        bid = DAILY_SALARY * 0.6  # Moderate bid (90)

    # Opponent analysis from previous_trace
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # Scenario 1: Opponents were very aggressive yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.85:  # highest_prev_bid >= 127.5
            if my_status['hp'] > 5:  # My HP is good, I can afford to let them fight and save budget
                # This is a strategic pass to let others exhaust budget.
                bid = min(bid, DAILY_SALARY * 0.4)  # 60
            else:  # My HP is not good enough (<=5), I need water, so I must compete
                bid = max(bid, highest_prev_bid + 2.5)  # Try to outbid them, with a buffer
                bid = min(bid, DAILY_SALARY * 0.99)  # Cap it just below full salary
        
        # Scenario 2: Opponents were moderately aggressive yesterday
        elif highest_prev_bid >= DAILY_SALARY * 0.5:  # highest_prev_bid between 75 and 127.5
            bid = max(bid, highest_prev_bid + 1.5)  # Slightly outbid, but also consider my HP-based bid
        
        # Scenario 3: Opponents were generally conservative yesterday
        else:  # highest_prev_bid < 75
            # If my HP is low, still bid reasonably to secure water.
            # If my HP is good, don't overpay.
            if my_status['hp'] < 5:
                bid = max(bid, DAILY_SALARY * 0.65)  # 97.5
            else:
                bid = max(bid, DAILY_SALARY * 0.55)  # 82.5

    # End-game aggression: If few days left and HP is not full, become more aggressive.
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 3 and my_status['hp'] < 10:
        bid = max(bid, DAILY_SALARY * 0.95)  # Push hard in the final days if not at full HP

    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], bid)
    
    # Ensure bid is always positive, even if budget is very low (to participate)
    final_bid = max(0.01, final_bid)

    return float(final_bid)
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_active_opponents = len(alive_opponents)

    if num_active_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid strategy based on HP and game stage
    if my_hp <= 3:
        # Critical HP, bid aggressively to survive
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 5 and current_day > EPISODE_DAYS / 2:
        # Moderate HP in mid-late game, be competitive
        base_bid = DAILY_SALARY * 0.8
    else:
        # Healthy HP, try to conserve budget but still win
        base_bid = DAILY_SALARY * 0.7

    # Adjust based on yesterday's highest opponent bid for competitive edge
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # Ensure we are always slightly above their highest known bid, if it's lower than our current base
        if base_bid < highest_prev_bid + 5:
             base_bid = highest_prev_bid + 5

        # If opponents are consistently bidding very high, push harder
        if highest_prev_bid > DAILY_SALARY * 0.7: # e.g., if their bid > 105
            base_bid = max(base_bid, highest_prev_bid + 10)

    # Apply a slight increase towards the end of the round to maintain pressure
    if current_day > EPISODE_DAYS / 2:
        base_bid += (current_day - EPISODE_DAYS / 2) * 0.5

    # Ensure bid is within budget and reasonable limits
    final_bid = min(my_budget, base_bid)
    final_bid = max(1.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)
    num_active_bidders = num_alive_opponents + 1 # Including myself

    # Calculate available water slots based on current supply
    available_water_slots = int(day_context['supply'] / WATER_REQ)

    # Default bid amount
    bid_amount = DAILY_SALARY * 0.5

    # Strategy 1: No opponents left, bid minimally to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Strategy 2: Critical HP, bid aggressively to survive
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # Strategy 3: End game, secure water
    if day_context['day'] >= EPISODE_DAYS - 2:
        # If supply is very low compared to demand, bid very high
        if available_water_slots < num_active_bidders:
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.7)

    # Strategy 4: React to yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # Determine competition level
        if available_water_slots < num_active_bidders: # High competition
            if my_status['hp'] <= 4: # Moderate HP, need to be competitive
                bid_amount = max(highest_prev_bid + 5, DAILY_SALARY * 0.7)
            else: # Good HP, still competitive but can be slightly less aggressive
                bid_amount = max(average_prev_bid * 1.1, DAILY_SALARY * 0.6)
        else: # Low competition (supply is abundant)
            if my_status['hp'] <= 4: # Still need water, but can be cheaper
                bid_amount = max(average_prev_bid * 0.9, DAILY_SALARY * 0.45)
            else: # Good HP, save money
                bid_amount = max(average_prev_bid * 0.8, DAILY_SALARY * 0.35)
    else:
        # Day 1 or no bids from yesterday, use a default strategy
        if available_water_slots < num_active_bidders: # High competition
            bid_amount = DAILY_SALARY * 0.65
        else: # Low competition
            bid_amount = DAILY_SALARY * 0.4

    # Ensure bid is within budget and non-negative
    return max(0.0, min(my_status['budget'], bid_amount))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no active opponents, bid minimally to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Calculate estimated competition level based on supply
    # If supply is less than or equal to my requirement, it's very competitive
    # Using int() for comparison as per CRITICAL INDEX RULE, although not an index.
    available_water_units = int(day_context['supply'] // WATER_REQ)
    num_competitors = len(alive_opponents) + 1 # Me plus active opponents

    is_supply_tight = available_water_units < num_competitors
    
    # Base bid if no specific strategy applies
    # A bid that ensures I can cover my water cost, potentially slightly higher
    base_bid = DAILY_SALARY * (WATER_REQ / day_context['supply']) if day_context['supply'] > 0 else DAILY_SALARY * 0.8
    base_bid = max(base_bid, DAILY_SALARY * 0.4) # Ensure a reasonable floor

    # If no yesterday bids (e.g., Day 1 of the episode or no one bid)
    if not yesterday_bids:
        if my_status['hp'] <= 2 or is_supply_tight:
            # Critical HP or tight supply, bid aggressively from the start
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        else:
            # Moderate starting bid
            return min(my_status['budget'], DAILY_SALARY * 0.55)

    # If yesterday bids exist, adapt strategy
    highest_prev_bid = max(yesterday_bids)

    # Strategy for low HP or if I missed water yesterday
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        # Bid very aggressively to survive or get water
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    # Strategy based on opponent's highest previous bid and supply tightness
    if highest_prev_bid >= DAILY_SALARY * 0.85 or is_supply_tight:
        # Opponents are bidding very high or supply is tight
        # If my HP is good and supply is not super tight, try to conserve if possible
        if my_status['hp'] > 3 and not is_supply_tight:
            return min(my_status['budget'], DAILY_SALARY * 0.3)
        else:
            # Outbid the highest previous bid, ensuring a strong bid for survival
            return min(my_status['budget'], max(base_bid, highest_prev_bid + 5.0, DAILY_SALARY * 0.9))
    else:
        # Moderate competition, or enough supply. Outbid slightly.
        return min(my_status['budget'], max(base_bid, highest_prev_bid + 1.5))
"""
