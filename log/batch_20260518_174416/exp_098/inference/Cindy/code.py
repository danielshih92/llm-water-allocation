# ============================================================
# Experiment: exp_098
# Agent: Cindy
# Source: exp_098
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    bid = DAILY_SALARY * 0.4

    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        bid = DAILY_SALARY * 0.9
        if day_context['day'] >= EPISODE_DAYS - 2:
            bid = DAILY_SALARY * 0.95

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    total_opponent_water_req = sum(o['water_requirement'] for o in alive_opponents)
    total_demand = WATER_REQ + total_opponent_water_req
    current_supply = day_context['supply']

    if current_supply < total_demand:
        if highest_prev_bid > DAILY_SALARY * 0.6:
            bid = max(bid, highest_prev_bid + 5)

        scarcity_ratio = total_demand / current_supply
        if scarcity_ratio > 1.5:
            bid = max(bid, DAILY_SALARY * 0.8)
        elif scarcity_ratio > 1.1:
            bid = max(bid, DAILY_SALARY * 0.65)
            
    else:
        if my_status['hp'] > 2 and my_status['no_water_days'] == 0:
            bid = min(bid, DAILY_SALARY * 0.3)
        if highest_prev_bid > DAILY_SALARY * 0.5:
            bid = max(bid, DAILY_SALARY * 0.4)

    bid = min(bid, my_status['budget'])
    bid = max(bid, 0.0)

    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    my_water_requirement = 13
    my_daily_salary = 150
    episode_days = 10 

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to conserve budget
    if not alive_opponents:
        return min(my_budget, my_daily_salary * 0.1)

    # Gather yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Determine a base bid based on HP and competition
    bid_amount = 0

    if my_hp <= 2: # Critical HP, must get water
        # Bid very aggressively, potentially above daily salary if budget allows
        # Eric's max bid was 165, my salary is 150. I might need to exceed 150 to win.
        target_bid = my_daily_salary * 1.1 # Base aggressive bid: 165
        if highest_prev_bid > my_daily_salary * 0.8: # If others were already bidding high
            target_bid = max(target_bid, highest_prev_bid + 5.0) # Ensure outbid
        bid_amount = min(my_budget, target_bid)
    elif my_hp <= 5: # Low HP
        # Bid high enough to secure water, but not as desperate as critical HP
        target_bid = my_daily_salary * 0.8 # Base high bid: 120
        if highest_prev_bid > my_daily_salary * 0.6: # If others were bidding moderately high
            target_bid = max(target_bid, highest_prev_bid + 3.0) # Ensure outbid
        bid_amount = min(my_budget, target_bid)
    else: # Healthy HP
        # Try to be competitive but conservative
        if highest_prev_bid > my_daily_salary * 0.5: # If others bid above average
            target_bid = highest_prev_bid + 1.5 # Slightly outbid
        else:
            target_bid = my_daily_salary * 0.55 # A solid moderate bid: 82.5

        # Since only one full water allocation is typically possible, competition is high.
        # If there are many alive opponents, competition is higher.
        if len(alive_opponents) >= 2:
            target_bid = max(target_bid, my_daily_salary * 0.6) # Ensure competitive if multiple opponents
        
        bid_amount = min(my_budget, target_bid)

    # Ensure a minimum bid if budget allows, to stay in the game or signal presence
    if bid_amount < my_daily_salary * 0.1 and my_budget > my_daily_salary * 0.1:
        bid_amount = my_daily_salary * 0.1
    elif bid_amount < 1.0: # Ensure bid is at least 1 if budget is very low but not zero
        bid_amount = min(my_budget, 1.0) if my_budget > 0 else 0.0

    return bid_amount
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents_count = sum(1 for opp_data in opponents_status.values() if opp_data['alive'])
    
    # Base bid: aim for a significant portion of my daily salary
    base_bid = DAILY_SALARY * 0.65

    # Identify strong opponents based on meta-round context
    strong_opponents_ids = ["Bob", "David"]
    
    yesterday_strong_bids = []
    for agent_id, opp_data in opponents_status.items():
        if opp_data['alive'] and agent_id in strong_opponents_ids:
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_strong_bids.append(prev['bid'])

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP, need water desperately
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.85
    
    # Adjust bid based on opponent's previous bids
    if yesterday_strong_bids:
        highest_prev_strong_bid = max(yesterday_strong_bids)
        
        # If strong opponents are bidding high, I need to match or slightly exceed
        if highest_prev_strong_bid >= DAILY_SALARY * 0.7:
            base_bid = max(base_bid, highest_prev_strong_bid + 5) # Bid slightly higher
        elif highest_prev_strong_bid >= DAILY_SALARY * 0.5:
            base_bid = max(base_bid, highest_prev_strong_bid + 2)
            
    # Adjust bid based on supply and number of competitors
    num_competitors = alive_opponents_count + 1 # Including myself
    
    # If supply is very limited (e.g., only enough for one or two people)
    if current_supply < WATER_REQ * 2: # Less than enough for two players
        if my_status['hp'] <= 5: # If HP is not great, bid very high
            base_bid = max(base_bid, DAILY_SALARY * 0.9)
        else: # If HP is good, still need to be competitive
            base_bid = max(base_bid, DAILY_SALARY * 0.75)
    elif current_supply < WATER_REQ * num_competitors: # Not enough for everyone
         base_bid = max(base_bid, DAILY_SALARY * 0.7)

    # Late game pressure: if few days left and HP is not full, bid higher
    if current_day >= EPISODE_DAYS - 3 and my_status['hp'] < 10: # Last 3 days
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    
    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], base_bid)
    
    # Ensure bid is at least a minimum sensible amount if budget allows
    if final_bid < DAILY_SALARY * 0.1 and my_status['budget'] >= DAILY_SALARY * 0.1:
        final_bid = DAILY_SALARY * 0.1 # Don't bid too low if I can afford more

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    my_bid = 0.0

    # Given supply range (15-25) and WATER_REQ (13), typically only one agent
    # can get their full water requirement, making it a winner-take-all scenario.

    # Scenario 1: Critical survival mode (low HP or missed water yesterday)
    if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1:
        # Bid very aggressively to ensure water, potentially exceeding daily salary.
        if highest_prev_bid > DAILY_SALARY * 0.8:
            my_bid = highest_prev_bid + 5.0
        else:
            my_bid = DAILY_SALARY * 1.05 # Bid slightly above salary
    
    # Scenario 2: Normal operation (HP is good)
    else:
        # Base bid is competitive, reflecting the high competition for water.
        base_competitive_bid = DAILY_SALARY * 0.75 # 112.5

        if highest_prev_bid > 0:
            # Bid slightly above the highest previous bid to win, but not excessively.
            my_bid = max(base_competitive_bid, highest_prev_bid + 1.5)
        else:
            # If no previous bids (e.g., Day 1), start with a strong competitive bid.
            my_bid = base_competitive_bid

        # If many opponents are still alive, ensure bid is sufficiently high
        if len(alive_opponents) > 1:
            my_bid = max(my_bid, DAILY_SALARY * 0.8)

    # Final checks: Ensure bid doesn't exceed budget and is at least 1.0
    final_bid = min(my_status['budget'], my_bid)
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

    current_day = day_context['day']
    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_current_budget, DAILY_SALARY * 0.1)

    david_alive = False
    david_yesterday_bid = 0.0
    other_opponents_max_bid = 0.0

    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                bid = prev_trace['bid']
                if opp_id == "David":
                    david_alive = True
                    david_yesterday_bid = bid
                else:
                    other_opponents_max_bid = max(other_opponents_max_bid, bid)

    base_bid = DAILY_SALARY * 0.5

    if my_current_hp <= 2 or my_no_water_days >= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_current_hp <= 5 or my_no_water_days >= 1:
        base_bid = DAILY_SALARY * 0.75

    if david_alive:
        if david_yesterday_bid > 0:
            if david_yesterday_bid >= DAILY_SALARY * 0.8:
                if my_current_hp <= 5 or my_no_water_days >= 1:
                    base_bid = max(base_bid, david_yesterday_bid + 5.0)
                else:
                    base_bid = max(base_bid, david_yesterday_bid * 0.9)
            elif david_yesterday_bid >= DAILY_SALARY * 0.5:
                base_bid = max(base_bid, david_yesterday_bid + 2.0)
            else:
                base_bid = max(base_bid, david_yesterday_bid + 1.0)

    if not david_alive or other_opponents_max_bid > david_yesterday_bid:
        if other_opponents_max_bid > 0:
            if other_opponents_max_bid >= DAILY_SALARY * 0.6 and (my_current_hp <= 5 or my_no_water_days >= 1):
                 base_bid = max(base_bid, other_opponents_max_bid + 2.0)
            else:
                base_bid = max(base_bid, other_opponents_max_bid + 0.5)

    final_bid = min(my_current_budget, base_bid)
    return max(0.1, final_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    # Default bid values
    base_bid = DAILY_SALARY * 0.55 # Start with a moderate bid

    # Check for critical HP or consecutive no-water days
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        # Desperate situation, bid very aggressively
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        # Low HP, bid higher to secure water
        base_bid = DAILY_SALARY * 0.75

    # Identify Alex and their previous bid
    alex_previous_bid = 0.0
    is_alex_alive = False
    for opp_id, opp in opponents_status.items():
        if opp_id == "Alex" and opp['alive']:
            is_alex_alive = True
            prev_trace = opp.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                alex_previous_bid = prev_trace['bid']
            break

    # Adjust bid based on Alex's behavior and supply
    if is_alex_alive:
        # If Alex bid high previously, or supply is tight, react
        if alex_previous_bid > DAILY_SALARY * 0.6 or day_context['supply'] < WATER_REQ * 2:
            # If desperate or supply is very tight, try to outbid Alex
            if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1 or day_context['supply'] < WATER_REQ * 1.5:
                base_bid = max(base_bid, alex_previous_bid + 5.0) # Bid more aggressively than Alex
            else:
                # Otherwise, stay competitive but try to save
                base_bid = max(base_bid, alex_previous_bid + 1.0) # Slightly above Alex
        elif alex_previous_bid > 0: # Alex is alive but didn't bid very high previously
            base_bid = max(base_bid, alex_previous_bid * 1.05) # Slightly above Alex's bid to win

    # If no Alex or Alex is not bidding significantly, consider other factors
    # Adjust for supply scarcity - supply range is [15, 25], WATER_REQ is 13
    # This block will always execute as supply is always < WATER_REQ * 2 (26)
    if day_context['supply'] <= WATER_REQ + 5: # e.g., supply 15-18, very tight
         base_bid = max(base_bid, DAILY_SALARY * 0.7)
    else: # supply 19-25, still competitive but less critical
         base_bid = max(base_bid, DAILY_SALARY * 0.6)

    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], base_bid)
    
    # Ensure a minimum bid to participate
    if final_bid < 1.0:
        final_bid = 1.0

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid: aim for profitability if possible, but prioritize survival
    # Start with a bid that attempts to profit, e.g., 60% of daily salary
    base_bid = DAILY_SALARY * 0.6

    # --- Adjust bid based on my HP ---
    if my_hp <= 2: # Critical HP: must get water
        base_bid = DAILY_SALARY * 1.4 # Very aggressive
    elif my_hp <= 4: # Low HP: need water urgently
        base_bid = DAILY_SALARY * 1.1 # Aggressive
    elif my_hp <= 6: # Medium HP: cautious, but can still take some risk
        base_bid = DAILY_SALARY * 0.9 # Slightly above break-even
    else: # Healthy HP: try to profit
        base_bid = DAILY_SALARY * 0.7 # Profitable bid

    # --- Adjust bid based on day (increasing desperation towards end) ---
    # As days progress, agents might bid higher to ensure survival
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        base_bid *= 1.15 # Increase bid significantly
    elif current_day >= EPISODE_DAYS - 4: # Last 4 days
        base_bid *= 1.07 # Increase bid moderately

    # --- Adjust bid based on supply scarcity ---
    # Supply is always scarce, but extremely low supply might warrant higher bids.
    # Scale supply from 0 (MIN_SUPPLY) to 1 (MAX_SUPPLY)
    supply_normalized = (current_supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    # If supply is low (normalized close to 0), increase bid. If high (normalized close to 1), slightly decrease.
    # Example: At min supply (0), multiplier 1.1. At max supply (1), multiplier 0.9.
    supply_modifier = 1.1 - (supply_normalized * 0.2)
    base_bid *= supply_modifier

    # --- Adjust bid based on opponent's previous bids ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        max_opp_bid = max(yesterday_bids)
        avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents were bidding very high, we must be competitive
        if max_opp_bid > DAILY_SALARY * 1.0: # If highest bid was above break-even
            base_bid = max(base_bid, max_opp_bid + 5.0) # Try to outbid the highest by a small margin
        elif max_opp_bid > DAILY_SALARY * 0.8: # If highest bid was moderately high
            base_bid = max(base_bid, avg_opp_bid + 2.0) # Try to be slightly above average
        # If opponents were bidding low, our base_bid (which aims for profit) should be fine,
        # but ensure it's at least competitive enough to win.
        else:
            base_bid = max(base_bid, avg_opp_bid * 1.05) # bid slightly above their average if they bid low

    # Ensure bid is not negative or zero
    final_bid = max(1.0, base_bid)

    # Critical override: If budget is very low and HP is critical, bid almost all budget to survive
    if my_budget < DAILY_SALARY * 0.75 and my_hp <= 3:
        final_bid = my_budget * 0.98
    # Ensure bid does not exceed available budget
    final_bid = min(my_budget, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    TOTAL_DAYS = 10 # From meta_round_state

    # In this specific scenario (supply 15-25, water_req 13), only one agent can get water per day.
    # This makes competition for water extremely fierce.

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimally to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's highest bid from all alive opponents' previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    current_day = day_context['day']
    days_remaining = TOTAL_DAYS - current_day

    # Aggressive bidding if HP is low (at risk of dying in 2 days or less) or it's late in the game
    if my_status['hp'] <= WATER_REQ * 2 or days_remaining <= 2:
        # Base aggressive bid
        bid_amount = DAILY_SALARY * 0.95

        # If there was a high bid yesterday, try to outbid it significantly for survival
        if highest_prev_bid > 0:
            bid_amount = max(bid_amount, highest_prev_bid + 5) # Bid slightly above opponent's highest previous bid
        
        # If it's the very last day and still alive, bid everything to survive
        if days_remaining == 0 and my_status['hp'] > 0: # Day 10 (last day) and still has HP
            bid_amount = my_status['budget']

        return min(my_status['budget'], bid_amount)

    # Moderate bidding for normal days to conserve budget
    else:
        # If opponents had high bids yesterday, try to bid just above them
        if highest_prev_bid >= DAILY_SALARY * 0.7: # Consider a high bid from yesterday as a threat
            bid_amount = highest_prev_bid + 1
        elif highest_prev_bid > 0: # Any other previous bid
            bid_amount = highest_prev_bid + 1
        else: # No significant previous bids from opponents, or day 1
            bid_amount = DAILY_SALARY * 0.6 # Moderate base bid

        # Cap normal bids to prevent overspending and ensure a minimum
        bid_amount = min(bid_amount, DAILY_SALARY * 0.9)
        bid_amount = max(bid_amount, DAILY_SALARY * 0.3) # Ensure a reasonable minimum bid

        return min(my_status['budget'], bid_amount)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    potential_winners = int(day_context['supply'] // WATER_REQ)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_prev_bid = 0
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)

    current_bid = DAILY_SALARY * 0.55

    if my_status['hp'] <= 1:
        current_bid = DAILY_SALARY * 1.2
    elif my_status['hp'] == 2:
        current_bid = DAILY_SALARY * 1.0
    elif my_status['hp'] == 3:
        current_bid = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 5:
        current_bid = DAILY_SALARY * 0.8
    
    if my_status['hp'] > 3:
        if max_prev_bid > DAILY_SALARY * 0.8:
            if num_alive_opponents + 1 > potential_winners:
                current_bid = max(current_bid, max_prev_bid + 5)
            else:
                current_bid = max(current_bid, max_prev_bid + 2)
        elif max_prev_bid > DAILY_SALARY * 0.5:
            current_bid = max(current_bid, max_prev_bid + 1)
        elif max_prev_bid > 0:
            current_bid = max(current_bid, DAILY_SALARY * 0.4, max_prev_bid + 1)
        else:
            if num_alive_opponents + 1 > potential_winners:
                current_bid = DAILY_SALARY * 0.7
            else:
                current_bid = DAILY_SALARY * 0.5

    final_bid = min(my_status['budget'], current_bid)

    return max(0.0, final_bid)
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
    
    bid_value = DAILY_SALARY * 0.9 # Default slightly below salary to save

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid very low to save money
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    # 1. Adjust bid based on my HP
    if my_hp <= 2: # Critical HP
        bid_value = DAILY_SALARY * 1.5
    elif my_hp <= 5: # Low HP
        bid_value = DAILY_SALARY * 1.2
    elif my_hp >= 8: # Healthy, can afford to be slightly less aggressive
        bid_value = DAILY_SALARY * 0.9

    # 2. Analyze opponent's previous bids from yesterday's trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest previous bid was very high, we need to be competitive
        if highest_prev_bid >= DAILY_SALARY * 1.0:
            bid_value = max(bid_value, highest_prev_bid + 10) # Bid higher than them
        elif highest_prev_bid >= DAILY_SALARY * 0.7:
            bid_value = max(bid_value, highest_prev_bid + 5) # Slightly higher
        else: # Opponents were less aggressive, try to win cheaply but still win
            bid_value = max(bid_value, highest_prev_bid * 1.05) # Just above

    # 3. Adjust based on supply scarcity
    available_slots = int(current_supply // WATER_REQ)
    
    if available_slots < num_alive_opponents + 1: # Scarcity
        bid_value *= 1.15
    elif available_slots >= num_alive_opponents + 2: # Abundant
        bid_value *= 0.95

    # 4. Adjust based on remaining days (end game pressure)
    remaining_days = TOTAL_DAYS - current_day
    if remaining_days <= 3: # Last 3 days
        if my_hp < 7: # Low HP late game, bid very aggressively
            bid_value = max(bid_value, DAILY_SALARY * 1.4)
        elif my_hp < 10: # Moderate HP late game
            bid_value = max(bid_value, DAILY_SALARY * 1.2)
    
    # Ensure bid does not exceed budget
    final_bid = min(my_budget, bid_value)

    # Ensure bid is at least a minimal amount if budget allows, to signal intent or win cheap water
    if final_bid <= 0 and my_budget > 0:
        final_bid = min(my_budget, 1.0) # Bid a token amount if budget is low but not zero
    elif final_bid <= 0 and my_budget <= 0:
        return 0.0 # No budget, cannot bid

    # Ensure bid is not negative
    final_bid = max(0.0, final_bid)

    return final_bid
"""
