# ============================================================
# Experiment: exp_075
# Agent: Cindy
# Source: exp_075
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
    EPISODE_DAYS = 10 # Based on Current Meta-Round State

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to get water
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Analyze opponent's previous bids and states
    highest_prev_bid = 0
    total_prev_bids = 0
    num_valid_prev_bids = 0
    opponents_critical_hp = 0 # Opponents with HP <= 2
    opponents_needing_water_yesterday = 0 # Opponents who lost HP yesterday

    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev_trace = opp.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                bid_val = prev_trace['bid']
                highest_prev_bid = max(highest_prev_bid, bid_val)
                total_prev_bids += bid_val
                num_valid_prev_bids += 1
            
            if opp['hp'] <= 2:
                opponents_critical_hp += 1
            if prev_trace and prev_trace.get('status') == 'HP_LOSS':
                opponents_needing_water_yesterday += 1

    avg_prev_bid = total_prev_bids / num_valid_prev_bids if num_valid_prev_bids > 0 else DAILY_SALARY * 0.5

    # Determine base bid strategy
    bid = 0

    # Emergency state: My HP is very low
    if my_status['hp'] <= 2:
        # Bid aggressively to survive
        bid = DAILY_SALARY * 0.95 # Base 142.5
        # If opponents are also critical or needed water, might need to bid even higher
        if opponents_critical_hp > 0 or opponents_needing_water_yesterday > 0:
            bid = DAILY_SALARY * 0.98 # 147
        # If supply is very low, competition is intense
        if day_context['supply'] <= MIN_SUPPLY + 2: # 17
            bid = DAILY_SALARY # 150
        
    # Critical state: My HP is moderate (3)
    elif my_status['hp'] == 3:
        # Need water, but can afford to be slightly less desperate than HP<=2
        bid = DAILY_SALARY * 0.8 # Base 120
        # If highest previous bid was high, try to beat it
        if highest_prev_bid > bid:
            bid = highest_prev_bid + 1
        # If many opponents are critical or needed water yesterday, increase bid
        if opponents_critical_hp >= num_alive_opponents / 2 or opponents_needing_water_yesterday >= num_alive_opponents / 2:
            bid = max(bid, DAILY_SALARY * 0.85) # 127.5
        # Adjust for supply: lower supply means higher competition
        if day_context['supply'] <= MIN_SUPPLY + 5: # 20
            bid += DAILY_SALARY * 0.05 # 7.5
        
    # Stable state: My HP is good (4 or 5)
    else: # my_status['hp'] >= 4
        # Can afford to save, but still aim for water if possible
        bid = DAILY_SALARY * 0.65 # Base 97.5
        # If highest previous bid was moderate, try to beat it slightly
        if highest_prev_bid > bid:
            bid = highest_prev_bid + 0.5
        # If opponents seem to be bidding low, I can also bid lower
        if highest_prev_bid < DAILY_SALARY * 0.7 and avg_prev_bid < DAILY_SALARY * 0.6: # 105 and 90
            bid = min(bid, DAILY_SALARY * 0.55) # 82.5
        # If supply is high, I can be more conservative
        if day_context['supply'] > MAX_SUPPLY - 5: # 20
            bid = min(bid, DAILY_SALARY * 0.6) # 90
        # If it's late in the game, and I have good HP, I might push harder to eliminate opponents
        if day_context['day'] >= EPISODE_DAYS - 2 and my_status['hp'] >= 4:
            bid = max(bid, DAILY_SALARY * 0.75) # 112.5

    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], bid)
    
    # Ensure bid is at least 0.1 to register
    final_bid = max(0.1, final_bid)

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

    # My maximum value for water (13 units) is my daily salary, as it enables earning that salary.
    my_max_value_for_water = DAILY_SALARY

    # --- Initial bid based on my health and remaining days ---
    # Default aggressive bid, as supply is always tight for my water_req
    bid_value = DAILY_SALARY * 0.85 

    # If very low HP or missed water, bid very high
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        bid_value = DAILY_SALARY * 0.98 # Almost max value to guarantee water

    # If HP is low but not critical
    elif my_status['hp'] <= 4:
        bid_value = DAILY_SALARY * 0.9

    # Adjust for end game: be more aggressive to secure survival
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2:
        bid_value = max(bid_value, DAILY_SALARY * 0.95) # Ensure high bid in final days

    # --- Adjust based on Opponents' previous bids ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids and num_alive_opponents > 0:
        max_yesterday_bid = max(yesterday_bids)
        
        # Since supply is always tight for 13 units (supply 15-25), we must outbid.
        # If healthy, try to win by a small margin.
        if my_status['hp'] > 4 and my_status['no_water_days'] == 0:
            bid_value = max(bid_value, max_yesterday_bid + 2.0)
            # Cap if opponents bid irrationally high, but still competitive
            bid_value = min(bid_value, my_max_value_for_water * 1.05) 
        else:
            # If not healthy, be more aggressive to ensure water
            bid_value = max(bid_value, max_yesterday_bid + 5.0)
            # Higher cap when desperate to secure water
            bid_value = min(bid_value, my_max_value_for_water * 1.1) 

    # If no opponents, bid minimum to save money
    if num_alive_opponents == 0:
        bid_value = 1.0

    # Ensure bid does not exceed budget and is at least 1.0
    final_bid = min(my_status['budget'], bid_value)
    final_bid = max(1.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    # Count alive opponents and find highest previous bid
    highest_prev_bid = 0.0
    num_alive_opponents = 0
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            num_alive_opponents += 1
            if opp_data.get('previous_trace') and opp_data['previous_trace'].get('bid') is not None:
                highest_prev_bid = max(highest_prev_bid, opp_data['previous_trace']['bid'])

    # If no opponents are alive, bid minimally to save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Base bid strategy based on my HP
    bid = 0.0
    if my_status['hp'] <= 2:
        bid = DAILY_SALARY * 1.15 # Very aggressive to survive
    elif my_status['hp'] <= 5:
        bid = DAILY_SALARY * 0.95 # Aggressive
    else:
        bid = DAILY_SALARY * 0.75 # Moderate

    # Adjust bid based on opponent's previous day bids
    # If there were significant previous bids, try to outbid the highest one slightly
    if highest_prev_bid > DAILY_SALARY * 0.3: # Only consider significant previous bids
        bid = max(bid, highest_prev_bid + 5) # Add a small buffer to win

    # Adjust bid based on supply scarcity
    # Given WATER_REQ = 13 and supply range [15, 25], water is always highly competitive.
    # If supply is very low (e.g., only enough for one agent if they all need 13), increase bid.
    if day_context['supply'] <= WATER_REQ + 5: # Supply is 15-18, very tight
        bid *= 1.05 # Slightly increase bid due to scarcity

    # Adjust bid based on game day (end game aggression vs. early game conservation)
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: # Last 2 days, be more aggressive to secure survival
        bid *= 1.1
    elif day_context['day'] <= 3 and my_status['hp'] > 7: # Early game, if healthy, can be slightly less aggressive
        bid *= 0.95

    # Ensure bid does not exceed current budget
    bid = min(my_status['budget'], bid)

    # Ensure bid is not negative
    bid = max(0.0, bid)

    return float(bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget'] # This already includes today's salary
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to get water
    if not alive_opponents:
        return max(1.0, min(my_budget, DAILY_SALARY * 0.1))

    # Base bid strategy
    bid = DAILY_SALARY * 0.8 # Default bid (120)

    # Aggression based on my HP
    if my_hp <= 2: # Critical HP, must win
        bid = DAILY_SALARY * 1.1 # 165
    elif my_hp <= 4: # Low HP
        bid = DAILY_SALARY * 0.95 # 142.5

    # Aggression based on game day (late game)
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        bid = max(bid, DAILY_SALARY * 1.05) # 157.5

    # Analyze opponent's previous bids to set a competitive bid
    highest_prev_bid = 0.0
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev_trace['bid'])

    if highest_prev_bid > 0:
        # If opponents were generally aggressive, bid slightly above their highest
        if highest_prev_bid >= DAILY_SALARY * 0.8: # If highest bid was 120 or more
            bid = max(bid, highest_prev_bid + (DAILY_SALARY * 0.05)) # Add 5% of salary margin
        else: # If highest bid was relatively low, still try to win but don't overspend
            bid = max(bid, highest_prev_bid + (DAILY_SALARY * 0.01)) # Add 1% margin

    # Final bid capping logic
    hard_cap = DAILY_SALARY * 1.5 # Absolute maximum bid (225) to avoid runaway debt

    # Determine if I'm in a desperate state
    desperate = (my_hp <= 2) or (current_day >= EPISODE_DAYS - 2) or (my_no_water_days > 0)

    if desperate:
        # If desperate, bid aggressively, potentially going into debt, capped by hard_cap
        final_bid = min(bid, hard_cap)
    else:
        # If not desperate, try to stay within current budget (`my_budget`).
        # However, if the calculated `bid` is higher than `my_budget`,
        # and `highest_prev_bid` suggests strong competition (e.g., > 90% of my_budget),
        # I might still need to go slightly into debt to win, but not as aggressively as when desperate.
        if bid > my_budget:
            if highest_prev_bid > my_budget * 0.9: # Opponents are bidding high, might need to go above budget
                final_bid = min(bid, hard_cap) # Allow going into debt up to hard_cap
            else:
                final_bid = my_budget # Cap at current budget if opponents aren't pushing too hard
        else:
            final_bid = bid # If desired bid is within budget, just bid that

    # Ensure bid is at least 1.0 to participate.
    final_bid = max(1.0, final_bid)

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

    # Base bid calculation
    # Default to a competitive bid
    bid_amount = DAILY_SALARY * 0.75

    # Survival mode: If HP is low or no water days accumulating, bid very aggressively
    if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1:
        bid_amount = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5:
        bid_amount = DAILY_SALARY * 0.85
    elif my_status['hp'] >= 8: # If healthy, can try to save a bit
        bid_amount = DAILY_SALARY * 0.65

    # Consider opponent's previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If I'm in survival mode, ensure I outbid the highest previous bid if possible
        if my_status['hp'] <= 5 or my_status['no_water_days'] >= 1:
            bid_amount = max(bid_amount, highest_prev_bid + 5)
        else:
            # If healthy, try to win but don't overspend blindly
            # If prev bids were high, still need to be competitive
            if highest_prev_bid > DAILY_SALARY * 0.7:
                 bid_amount = max(bid_amount, highest_prev_bid + 1)
            else:
                 bid_amount = max(bid_amount, highest_prev_bid * 1.1)

    # Ensure bid doesn't exceed budget
    final_bid = min(my_status['budget'], bid_amount)

    # Ensure bid is at least a minimum amount if budget allows, to participate
    if final_bid <= 0 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], 1.0)
    elif final_bid < 0: # Safeguard for negative bids, though min() should prevent
        final_bid = 0.0

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    base_bid = DAILY_SALARY * 0.85

    supply = day_context['supply']
    if supply <= 17.0:
        base_bid *= 1.1
    elif supply >= 23.0:
        base_bid *= 0.9

    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.98
    elif my_status['hp'] <= 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif my_status['hp'] >= 8:
        base_bid *= 0.95

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            if my_status['hp'] > 4:
                base_bid = max(base_bid, highest_prev_bid + 2)
            else:
                base_bid = max(base_bid, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.7:
            base_bid = max(base_bid, highest_prev_bid * 1.05)
    
    final_bid = min(my_status['budget'], base_bid)
    
    if my_status['hp'] <= 2 and my_status['budget'] > 0:
        final_bid = my_status['budget']
    
    final_bid = max(1.0, final_bid)

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
    
    # Given supply range [15, 25] and WATER_REQ = 13,
    # at most one agent can fully satisfy their water requirement (2*13=26 > 25).
    # This implies extremely high competition for water.
    
    # Base bid: very aggressive due to high competition
    # Start with a high percentage of daily salary
    base_bid = DAILY_SALARY * 0.85 # 127.5

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents are alive, bid minimally to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1) # Bid very low if no competition

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_bid = base_bid

    # Adjust bid based on opponent's previous behavior and my HP
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If my HP is critical (3 or less), bid extremely aggressively
        if my_status['hp'] <= 3:
            # Bid a very high percentage of salary, ensuring it's at least slightly above highest previous bid
            current_bid = max(DAILY_SALARY * 0.99, highest_prev_bid + 10) 
        else: # My HP is not critical, but competition is still high
            # Bid to win, slightly above highest previous bid, but not less than base_bid
            current_bid = max(base_bid, highest_prev_bid + 5)
    else: # No previous bids (e.g., Day 1 or opponents didn't bid yesterday)
        if my_status['hp'] <= 3:
            current_bid = DAILY_SALARY * 0.99 # Start very high if desperate
        else:
            current_bid = base_bid # Use base bid

    # Adjust based on day progress (water becomes more valuable later)
    day_factor = 1 + (day_context['day'] / EPISODE_DAYS) * 0.15 # Increase bid by up to 15% by last day
    current_bid *= day_factor

    # Adjust for very tight supply (though always tight for full WATER_REQ)
    # If supply is barely enough for one, might need to push a bit more
    if day_context['supply'] <= WATER_REQ + 2: # e.g., supply 15, 16, 17, 18, 19
        current_bid *= 1.03 # Small additional boost

    # Ensure bid does not exceed budget and is at least 1.0
    final_bid = min(my_status['budget'], current_bid)
    final_bid = max(1.0, final_bid)
    
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid: a percentage of daily salary, adjusted dynamically
    base_bid_value = DAILY_SALARY * 0.65

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        return max(0.01, min(my_status['budget'], DAILY_SALARY * 0.1))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Adjust base bid based on my HP
    if my_status['hp'] <= 2: # Critical HP
        base_bid_value = DAILY_SALARY * 0.98 # Almost max to survive
    elif my_status['hp'] <= 4: # Low HP
        base_bid_value = DAILY_SALARY * 0.85
    elif my_status['hp'] <= 7: # Moderate HP concern
        base_bid_value = DAILY_SALARY * 0.75

    # Adjust based on remaining days (become more aggressive late game)
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: # Last few days, push harder
        base_bid_value *= 1.1
    elif day_context['day'] <= 2 and my_status['hp'] > 5: # Early days, conserve if possible and not critical
        base_bid_value *= 0.9

    # Adjust based on supply scarcity
    # Calculate how many full water requirements can be met by the supply
    num_full_slots = int(day_context['supply'] // WATER_REQ)
    if num_full_slots == 0: # Supply less than my requirement, very high competition
        if my_status['hp'] <= 3: # Desperate
            base_bid_value = max(base_bid_value, DAILY_SALARY * 1.15) # Be willing to overbid
        else:
            base_bid_value = max(base_bid_value, DAILY_SALARY * 0.95)
    elif num_full_slots == 1 and num_alive_opponents >= 1: # Only one full slot available for multiple agents
        if my_status['hp'] <= 5:
            base_bid_value = max(base_bid_value, DAILY_SALARY * 1.05)
        else:
            base_bid_value = max(base_bid_value, DAILY_SALARY * 0.9)
    elif day_context['supply'] >= MAX_SUPPLY and my_status['hp'] > 5: # Abundant supply, can try to save
        base_bid_value *= 0.8

    # React to opponents' previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        lowest_prev_bid = min(yesterday_bids)

        # If highest previous bid was very high, we might need to exceed it
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            base_bid_value = max(base_bid_value, highest_prev_bid + 3) # Slightly overbid the highest
        # If highest previous bid was moderate but still competitive
        elif highest_prev_bid >= DAILY_SALARY * 0.55:
            base_bid_value = max(base_bid_value, highest_prev_bid + 1.5)
        # If bids were generally low, try to win cheaply, but not too cheap if others are still bidding
        elif highest_prev_bid < DAILY_SALARY * 0.4 and my_status['hp'] > 5:
            base_bid_value = min(base_bid_value, lowest_prev_bid + 1)
            base_bid_value = min(base_bid_value, DAILY_SALARY * 0.4)

    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], base_bid_value)

    # Ensure bid is at least 0.01 to avoid issues and indicate intent to bid
    return max(0.01, final_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQUIREMENT = 13
    MY_DAILY_SALARY = 150
    EPISODE_DAYS = 10 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Determine my urgency
    is_critical_hp = my_status['hp'] <= 2
    is_critical_no_water_days = my_status['no_water_days'] >= 1
    is_critical = is_critical_hp or is_critical_no_water_days

    # Base bid calculation
    base_bid = MY_DAILY_SALARY * 0.5

    if is_critical:
        base_bid = MY_DAILY_SALARY * 0.95 # Bid aggressively for survival
    elif my_status['hp'] >= (EPISODE_DAYS - day_context['day']) + 2: # High HP, can afford to save
        base_bid = MY_DAILY_SALARY * 0.3
    else:
        base_bid = MY_DAILY_SALARY * 0.6 # Moderate bid

    # Opponent bid analysis from previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    my_bid = base_bid

    if yesterday_bids:
        avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids)
        max_opp_bid = max(yesterday_bids)

        if is_critical:
            # If critical, try to outbid the highest opponent from yesterday
            my_bid = max(my_bid, max_opp_bid + 5)
        else:
            # Otherwise, bid slightly above average to stay competitive
            my_bid = max(my_bid, avg_opp_bid * 1.05)
    
    # Supply/Demand adjustment
    total_water_needed_by_others = sum(o['water_requirement'] for o in alive_opponents)
    total_demand = MY_WATER_REQUIREMENT + total_water_needed_by_others

    if total_demand > 0: # Avoid division by zero if no one needs water (unlikely)
        if day_context['supply'] < total_demand: # Scarce supply, increase bid
            my_bid *= 1.15
        elif day_context['supply'] >= total_demand * 1.5: # Abundant supply, decrease bid
            my_bid *= 0.85

    # Final bid constraints
    my_bid = min(my_bid, my_status['budget']) # Cannot bid more than budget
    
    if is_critical:
        # If critical, can bid more than daily salary to survive, up to a limit
        my_bid = min(my_bid, MY_DAILY_SALARY * 1.3) # Cap at 130% of salary
    else:
        # If not critical, aim for profitability
        my_bid = min(my_bid, MY_DAILY_SALARY * 0.95) # Cap at 95% of salary to ensure profit

    my_bid = max(my_bid, 1.0) # Ensure bid is at least 1.0, not 0 or negative

    return my_bid
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

    # If no opponents are alive, bid minimally to save budget.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Base bid, designed to be competitive for the single water slot.
    base_bid = DAILY_SALARY * 0.9

    # Adjustment for survival urgency
    if my_status['hp'] <= 2: # Critical health, must win at almost any cost
        return min(my_status['budget'], DAILY_SALARY * 1.25)
    if my_status['no_water_days'] > 0: # Missed water yesterday, need to win today
        return min(my_status['budget'], DAILY_SALARY * 1.15)

    # Analyze opponent's previous bids to inform today's bid
    highest_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])

    # Determine a target bid based on opponent's aggression and my salary
    target_bid = base_bid

    if highest_prev_bid > 0:
        # If opponents were aggressive, I need to bid higher to secure the slot.
        if highest_prev_bid >= DAILY_SALARY * 0.85: # If opponents were bidding very high
            target_bid = max(base_bid, highest_prev_bid + 7) # Bid slightly above
        elif highest_prev_bid >= DAILY_SALARY * 0.7: # If opponents were moderately high
            target_bid = max(base_bid, highest_prev_bid + 3)
        else: # Opponents were not very aggressive, but I still need to win the slot
            target_bid = max(base_bid, highest_prev_bid * 1.05) # Slightly higher than their highest
    
    # If it's late in the game (last two days), become more aggressive
    if day_context['day'] >= EPISODE_DAYS - 1:
        target_bid = max(target_bid, DAILY_SALARY * 1.1)

    # Ensure a strong floor for the bid, given high competition, then cap by budget
    target_bid = max(target_bid, DAILY_SALARY * 0.75)
    final_bid = min(my_status['budget'], target_bid)

    return final_bid
"""
