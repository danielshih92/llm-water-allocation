# ============================================================
# Experiment: exp_106
# Agent: Cindy
# Source: exp_106
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], 1)

    my_bid = 0.0
    if my_status['hp'] == 5:
        my_bid = DAILY_SALARY * 0.5
    elif my_status['hp'] == 4:
        my_bid = DAILY_SALARY * 0.6
    elif my_status['hp'] == 3:
        my_bid = DAILY_SALARY * 0.75
    elif my_status['hp'] == 2:
        my_bid = DAILY_SALARY * 0.9
    elif my_status['hp'] == 1:
        my_bid = DAILY_SALARY * 0.99
    else:
        my_bid = DAILY_SALARY * 0.5

    highest_prev_bid = 0.0
    opponent_high_budget_desperate_bids = []

    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev_trace = opp.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                highest_prev_bid = max(highest_prev_bid, prev_trace['bid'])

                is_opponent_desperate = opp['hp'] <= 2
                if is_opponent_desperate:
                    if opp['budget'] >= DAILY_SALARY * 2:
                        opponent_high_budget_desperate_bids.append(prev_trace['bid'])

    if highest_prev_bid > 0:
        if my_status['hp'] <= 2:
            my_bid = max(my_bid, highest_prev_bid + 5)
        elif my_status['hp'] == 3:
            my_bid = max(my_bid, highest_prev_bid + 2)
        else:
            my_bid = max(my_bid, highest_prev_bid + 1)

    if opponent_high_budget_desperate_bids:
        max_opp_high_budget_desperate_bid = max(opponent_high_budget_desperate_bids)
        if my_status['hp'] <= 3:
            my_bid = max(my_bid, max_opp_high_budget_desperate_bid + 10)
        else:
            my_bid = max(my_bid, max_opp_high_budget_desperate_bid + 5)

    my_bid = min(my_bid, my_status['budget'])
    my_bid = max(my_bid, 1)

    if my_status['hp'] > 1:
        my_bid = min(my_bid, DAILY_SALARY * 1.1)

    return my_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimal to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Calculate total water demand (including myself)
    total_water_demand = WATER_REQ
    for opp in alive_opponents:
        total_water_demand += opp['water_requirement']

    # --- Base Bid Logic ---
    # Default bid: a moderate fraction of daily salary
    base_bid = DAILY_SALARY * 0.55

    # Adjustment for HP
    if my_status['hp'] <= 2: # Critical HP, must get water
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5: # Low HP
        base_bid = DAILY_SALARY * 0.8
    # If HP is high, consider being less aggressive to save budget
    elif my_status['hp'] >= 8 and current_day > 1:
        base_bid = DAILY_SALARY * 0.45

    # Adjustment for supply scarcity
    if current_supply < total_water_demand:
        if current_supply < WATER_REQ: # Very scarce
            base_bid = max(base_bid, DAILY_SALARY * 0.9)
        else: # Moderately scarce
            base_bid = max(base_bid, DAILY_SALARY * 0.7)
    else: # Abundant supply
        base_bid = min(base_bid, DAILY_SALARY * 0.35)

    # --- Opponent Reaction based on previous_trace ---
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents are bidding very high
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3 and current_supply >= total_water_demand: # Healthy HP and good supply
                # Let them overbid, I can afford to bid lower
                base_bid = min(base_bid, DAILY_SALARY * 0.3)
            else: # Low HP or supply is scarce, must be competitive
                base_bid = max(base_bid, highest_prev_bid + (DAILY_SALARY * 0.05))
        # If opponents are bidding moderately high
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            if current_supply < total_water_demand / 2 or my_status['hp'] <= 5: # Supply tight or my HP low
                base_bid = max(base_bid, highest_prev_bid + (DAILY_SALARY * 0.02))
            else:
                base_bid = min(base_bid, highest_prev_bid * 0.9)

    # --- Final bid adjustments ---
    # Final bid cannot exceed budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure a minimum bid to participate
    final_bid = max(0.01, final_bid)

    # Last day strategy: bid all if needed
    if current_day == EPISODE_DAYS:
        final_bid = my_status['budget']

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

    # Start with a base bid that is competitive for survival
    # Opponents in previous meta-round bid high (avg 95-103, max 130).
    bid_amount = DAILY_SALARY * 0.65 # A good starting point

    # Adjust bid based on my HP urgency
    if my_status['hp'] <= 2: # Critical health, must win
        bid_amount = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low health
        bid_amount = DAILY_SALARY * 0.85
    elif my_status['no_water_days'] > 0: # Failed to get water recently, increase urgency
        bid_amount = max(bid_amount, DAILY_SALARY * 0.75)

    # Adjust bid based on day progression (late game urgency)
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: # Last 2 days, high urgency
        bid_amount = max(bid_amount, DAILY_SALARY * 0.9)
    elif remaining_days <= 4: # Last 4 days, increased urgency
        bid_amount = max(bid_amount, DAILY_SALARY * 0.75)

    # Analyze opponents' previous bids to react
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        # No opponents, bid minimum to conserve budget
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were aggressive yesterday, I need to be more aggressive
        # Add a small margin to try and outbid them consistently.
        if highest_prev_bid >= DAILY_SALARY * 0.7: # High previous competition
            bid_amount = max(bid_amount, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderate previous competition
            bid_amount = max(bid_amount, highest_prev_bid + 2)
        # If highest_prev_bid was very low, my current bid_amount should still be sufficient
        # and we don't want to reduce our bid based on potentially misleading low bids.

    # Adjust bid based on supply scarcity (low supply means higher competition)
    # Supply range: [15, 25]. My WATER_REQ = 13.
    # At supply 15-16, only one player can get their full requirement.
    if day_context['supply'] <= 16: # Very low supply, extremely competitive
        bid_amount = max(bid_amount, DAILY_SALARY * 0.9)
    elif day_context['supply'] <= 20: # Moderately low supply
        bid_amount = max(bid_amount, DAILY_SALARY * 0.7)

    # Ensure final bid does not exceed my current budget or my daily salary limit
    final_bid = min(my_status['budget'], bid_amount, DAILY_SALARY * 1.0)

    # Ensure bid is always positive
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From Current Meta-Round State

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents are alive, bid minimally to get water
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Base bid strategy
    # Default bid is moderate, aiming to conserve budget but secure water
    bid_amount = DAILY_SALARY * 0.55 # A good starting point for moderate competition

    # 1. Survival Bidding (Highest Priority)
    if my_hp <= 2: # Critical HP, must win
        bid_amount = DAILY_SALARY * 0.95
    elif my_hp <= 5 or my_no_water_days > 0: # Low HP or missed water yesterday
        bid_amount = DAILY_SALARY * 0.85
    
    # 2. React to Opponents' Yesterday's Bids (using previous_trace)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If yesterday's highest bid was high, I need to bid higher to win
        if highest_prev_bid >= DAILY_SALARY * 0.75: # High competition detected
            bid_amount = max(bid_amount, highest_prev_bid + 1.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.4: # Moderate competition
            bid_amount = max(bid_amount, highest_prev_bid + 0.5)
        # If highest_prev_bid was very low, my base bid might still be enough, or slightly adjusted
        # No else here, as bid_amount is already set based on HP and will be adjusted by other factors.

    # 3. Adjust based on Supply
    # Calculate total water requirement for all alive players (including myself)
    total_water_needed_approx = WATER_REQ * (num_alive_opponents + 1)

    if current_supply <= total_water_needed_approx: # Supply is tight or insufficient
        if my_hp <= 5: # If HP is low, be very aggressive in tight supply
            bid_amount = max(bid_amount, DAILY_SALARY * 0.9)
        else: # If HP is good, still be aggressive but not desperate
            bid_amount = max(bid_amount, DAILY_SALARY * 0.75)
    elif current_supply >= total_water_needed_approx * 1.5: # Abundant supply
        # If supply is abundant, we can afford to bid less, unless HP is critical
        if my_hp > 5:
            bid_amount = min(bid_amount, DAILY_SALARY * 0.45) # Conserve budget
        else: # Still need water, but maybe not top bid
            bid_amount = min(bid_amount, DAILY_SALARY * 0.7)

    # 4. Adjust based on Day Progression (more aggressive towards the end)
    if current_day >= EPISODE_DAYS * 0.7: # Last 30% of days
        bid_amount = max(bid_amount, DAILY_SALARY * 0.8) # Increase aggression
    elif current_day <= EPISODE_DAYS * 0.3: # First 30% of days
        # If early days and HP is good, try to conserve
        if my_hp > 5:
            bid_amount = min(bid_amount, DAILY_SALARY * 0.5)

    # Final bid cannot exceed budget
    final_bid = min(my_budget, bid_amount)
    
    # Ensure a positive bid if budget allows
    if final_bid <= 0 and my_budget > 0:
        return 1.0 # Bid minimum to try and get water
    elif final_bid <= 0: # No budget, can't bid
        return 0.0

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    current_day = day_context['day']
    total_supply = day_context['supply']

    # Calculate number of alive agents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_agents = len(alive_opponents) + 1 # Include myself

    # --- Base Bid Calculation ---
    # Start with a base bid that aims to secure water while saving some budget.
    # Given Alex and Bob's past aggression, a higher base is prudent.
    base_bid = DAILY_SALARY * 0.75

    # --- Adjust for My HP ---
    if my_status['hp'] <= 2: # Very critical HP
        base_bid = DAILY_SALARY * 0.95 # Bid aggressively to survive
    elif my_status['hp'] <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.85

    # --- Adjust for Supply Scarcity ---
    # If supply is low, competition will be higher.
    # Supply range is [15, 25].
    # Check if total supply is less than total potential demand
    if total_supply <= WATER_REQ * num_alive_agents: 
        base_bid *= 1.15 # Increase bid significantly if supply is very tight
    elif total_supply < (WATER_REQ * num_alive_agents) * 1.5: # Moderately tight supply
        base_bid *= 1.05
    elif total_supply >= 22: # Abundant supply
        base_bid *= 0.9 # Decrease bid if supply is plentiful

    # --- Adjust for Day of Episode (End Game Pressure) ---
    if current_day >= EPISODE_DAYS - 2: # Last 2-3 days
        if my_status['hp'] <= 5: # Need to survive to the end
            base_bid = max(base_bid, DAILY_SALARY * 0.95)
        else: # Aim to finish strong, but not overspend if not desperate
            base_bid = max(base_bid, DAILY_SALARY * 0.8)

    # --- Adjust for Opponent Behavior (Yesterday's Trace) ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If highest opponent bid was very high, react by slightly outbidding
        if max_yesterday_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, max_yesterday_bid * 1.02)

        # If average opponent bid is high, indicates general aggression
        if avg_yesterday_bid >= DAILY_SALARY * 0.75:
            base_bid = max(base_bid, avg_yesterday_bid * 1.01)

    # --- Final Bid Constraints ---
    final_bid = min(base_bid, my_status['budget']) # Cannot bid more than budget
    final_bid = max(final_bid, 0.0) # Bid cannot be negative

    # If my budget is very low and I'm desperate, bid whatever I have left
    if my_status['hp'] <= 1 and my_status['budget'] > 0:
        final_bid = my_status['budget']
    
    # Ensure a minimal bid to try and get water if budget allows, even if calculated bid is low
    if final_bid < WATER_REQ * 2 and my_status['budget'] >= WATER_REQ * 2:
        final_bid = max(final_bid, WATER_REQ * 2)

    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15.0
    MAX_SUPPLY = 25.0

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid very low to save budget, minimum 1.0 to get water.
    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    # Initialize bid_value to a competitive base, based on observed winning bids from previous meta-round.
    # Alex and Eric bid ~95 and survived. 95 / 150 = 0.633. So, start slightly above that.
    bid_value = DAILY_SALARY * 0.65 # Base bid: 97.5

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If the highest bid yesterday was already high, we need to be competitive.
        # Bid slightly above it to increase chances of winning, but only if it's a significant bid.
        if highest_prev_bid > DAILY_SALARY * 0.5: # Only react to significant bids (above 75)
            bid_value = max(bid_value, highest_prev_bid + 2.0) # Bid 2 units higher than highest previous

    # Adjust bid based on my HP (more desperate = higher bid)
    if my_status['hp'] <= 2: # Critical health, almost dead
        bid_value = DAILY_SALARY * 0.95 # 142.5
    elif my_status['hp'] <= 4: # Very low health
        bid_value = DAILY_SALARY * 0.85 # 127.5
    elif my_status['hp'] <= 6: # Low health
        bid_value = DAILY_SALARY * 0.75 # 112.5
    # If HP is > 6, bid_value remains as determined by base and highest_prev_bid

    # Adjust bid based on supply scarcity
    supply = day_context['supply']
    if supply == MIN_SUPPLY: # Very scarce water (15 units)
        bid_value *= 1.1 # Increase bid by 10% for maximum competition
    elif supply == MAX_SUPPLY: # More water available (25 units)
        bid_value *= 0.95 # Decrease bid by 5% to save budget, while remaining competitive

    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], bid_value)
    
    # Ensure bid is at least 1.0 if budget allows, otherwise 0.
    if my_status['budget'] >= 1.0:
        final_bid = max(1.0, final_bid)
    else:
        final_bid = 0.0 # Cannot bid if budget is less than 1.0

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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid strategy adjusted for my HP
    bid = DAILY_SALARY * 0.7 # Default competitive bid

    if my_hp <= 2: # Critical HP, must win
        bid = DAILY_SALARY * 1.2 # Bid aggressively (180)
        if highest_prev_bid > DAILY_SALARY * 0.9: # If opponents are already very high
            bid = max(bid, highest_prev_bid + 10) # Outbid them significantly
        elif highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid + 5)
    elif my_hp <= 4: # Low HP, need water
        bid = DAILY_SALARY * 1.05 # Aggressive bid (157.5)
        if highest_prev_bid > DAILY_SALARY * 0.8: # If opponents are high
            bid = max(bid, highest_prev_bid + 7)
        elif highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid + 3)
    else: # Healthy HP, can be more strategic
        if highest_prev_bid >= DAILY_SALARY * 1.05: # Opponents bidding very high (>157.5)
            bid = highest_prev_bid + 5 # Slightly outbid
        elif highest_prev_bid >= DAILY_SALARY * 0.9: # Opponents bidding high (>135)
            bid = max(DAILY_SALARY * 0.95, highest_prev_bid + 3) # Be competitive (142.5)
        elif highest_prev_bid >= DAILY_SALARY * 0.7: # Opponents bidding moderately (>105)
            bid = max(DAILY_SALARY * 0.8, highest_prev_bid + 2) # Be competitive (120)
        else: # Opponents bidding low or no previous bids
            bid = DAILY_SALARY * 0.7 # Base competitive bid (105)

    # Further adjustment for late game pressure
    if current_day >= EPISODE_DAYS * 0.8: # Last 20% of days
        bid *= 1.08 # Increase aggression significantly
    elif current_day >= EPISODE_DAYS * 0.5: # Mid-late game
        bid *= 1.03 # Slightly more aggressive

    # Ensure bid does not exceed available budget
    final_bid = min(my_budget, bid)

    # Ensure bid is at least 0
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    # Bid multipliers
    LOW_BID_MULTIPLIER = 0.3 # 45
    MODERATE_BID_MULTIPLIER = 0.6 # 90
    HIGH_BID_MULTIPLIER = 0.85 # 127.5
    VERY_HIGH_BID_MULTIPLIER = 0.95 # 142.5
    CRITICAL_BID_MULTIPLIER = 1.05 # 157.5 (can exceed daily salary if budget allows)

    # Opponent categories (from observation in LATEST METAROUND CONTEXT)
    STRONG_OPPONENTS = ["Alex", "David"]

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid minimal to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * LOW_BID_MULTIPLIER)

    # Calculate remaining days
    remaining_days = EPISODE_DAYS - day_context['day']

    # Aggressive bidding if HP is critically low or it's very late in the game
    if my_status['hp'] <= 1 or remaining_days == 0: # HP 1 or last day
        return min(my_status['budget'], DAILY_SALARY * CRITICAL_BID_MULTIPLIER)
    elif my_status['hp'] <= 3 or remaining_days <= 2: # HP 2-3 or last 2 days
        return min(my_status['budget'], DAILY_SALARY * VERY_HIGH_BID_MULTIPLIER)

    # Analyze yesterday's bids
    yesterday_bids = []
    strong_opponent_yesterday_bids = []

    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
                if opp_id in STRONG_OPPONENTS:
                    strong_opponent_yesterday_bids.append(prev['bid'])

    highest_overall_prev_bid = max(yesterday_bids) if yesterday_bids else 0
    highest_strong_prev_bid = max(strong_opponent_yesterday_bids) if strong_opponent_yesterday_bids else 0

    # Base bid, starting point for calculation
    # On first day or if no previous bids, start with a competitive bid
    if highest_overall_prev_bid == 0:
        base_bid = DAILY_SALARY * 0.75 # A competitive starting bid (112.5)
    else:
        base_bid = highest_overall_prev_bid + 1 # Default to slightly above previous highest

    # Adjust bid based on strong opponent behavior
    if highest_strong_prev_bid > 0:
        # If strong opponents are bidding high, we must compete
        if highest_strong_prev_bid >= DAILY_SALARY * HIGH_BID_MULTIPLIER:
            base_bid = max(base_bid, highest_strong_prev_bid + 5)
        elif highest_strong_prev_bid >= DAILY_SALARY * MODERATE_BID_MULTIPLIER:
            base_bid = max(base_bid, highest_strong_prev_bid + 2)
            
    # Further adjust bid based on my current HP
    if my_status['hp'] <= 5: # Moderate HP concern
        base_bid = max(base_bid, DAILY_SALARY * HIGH_BID_MULTIPLIER)
    elif my_status['hp'] <= 7: # Slight HP concern
        base_bid = max(base_bid, DAILY_SALARY * MODERATE_BID_MULTIPLIER)

    # Ensure bid doesn't exceed budget
    final_bid = min(my_status['budget'], base_bid)
    
    # Ensure a minimum bid to stay in contention, especially given supply == 1 slot for my WATER_REQ
    final_bid = max(final_bid, DAILY_SALARY * LOW_BID_MULTIPLIER) # At least 45

    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid conservatively but ensure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.5)

    # --- Determine base bid --- 
    # Start with a strong competitive bid, assuming competition from aggressive players
    base_bid = DAILY_SALARY * 0.75 

    # --- Adjust for HP --- 
    # Prioritize survival when HP is critical or low
    if my_status['hp'] <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.98
    elif my_status['hp'] <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.90

    # --- Analyze yesterday's bids from alive opponents ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    # --- Adjust bid based on opponent behavior ---
    current_bid = base_bid

    if max_yesterday_bid > 0:
        # If opponents were aggressive yesterday, try to outbid slightly
        if max_yesterday_bid >= DAILY_SALARY * 0.8: # High bids yesterday (e.g., David/Eric)
            current_bid = max(current_bid, max_yesterday_bid + 2.0)
        else: # Moderate bids yesterday
            current_bid = max(current_bid, max_yesterday_bid + 1.0)
    
    # --- Adjust for supply scarcity ---
    # Given WATER_REQ=13 and supply range [15, 25], competition for full water is always high.
    # If supply is very low (e.g., barely enough for one agent), be even more aggressive.
    if day_context['supply'] < WATER_REQ * 1.5: # e.g., supply < 19.5, indicating very tight supply
        current_bid = max(current_bid, DAILY_SALARY * 0.92) 

    # Ensure bid doesn't exceed current budget
    current_bid = min(current_bid, my_status['budget'])

    # Ensure a minimum bid to be competitive and reflect the value of water
    current_bid = max(current_bid, DAILY_SALARY * 0.5)

    # Ensure bid is not negative
    current_bid = max(0.0, current_bid)

    return current_bid
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
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']
    days_left = EPISODE_DAYS - current_day + 1

    # In this scenario (supply 15-25, water_req 13), only 1 agent can win water per day.
    # This means bidding will be highly competitive.

    # 1. Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev_trace = opp.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                yesterday_bids.append(prev_trace['bid'])
    
    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # 2. Determine my bid strategy based on my state and opponent behavior
    bid = 0.0

    # If HP is critical (0 or 1), bid everything to survive
    if my_hp <= 1:
        bid = my_budget
    # If I missed water yesterday and HP is low, bid very aggressively
    elif my_no_water_days > 0 and my_hp < 5:
        bid = DAILY_SALARY * 1.25
        if highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid + 10.0)
    # If HP is low (2-4), need to win
    elif my_hp < 5:
        bid = DAILY_SALARY * 1.1
        if highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid + 5.0)
    # If HP is moderate (5-7)
    elif my_hp < 8:
        bid = DAILY_SALARY * 1.0
        if highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid + 1.0)
    # If HP is high (8), can afford to be slightly less aggressive, but still competitive
    else: # my_hp == 8
        bid = DAILY_SALARY * 0.85 # Start conservative
        if highest_prev_bid > 0:
            # If opponent was very aggressive, try to stay relevant but don't overspend too much
            if highest_prev_bid > DAILY_SALARY * 1.1: 
                bid = max(bid, DAILY_SALARY * 0.95) 
            else: # Opponent bid moderately, try to slightly outbid
                bid = max(bid, highest_prev_bid + 1.0) 

        # If it's early in the game and I have high HP and good budget, I can be more conservative
        if current_day < EPISODE_DAYS / 2 and my_budget > DAILY_SALARY * 4: # Good budget buffer
            bid = min(bid, DAILY_SALARY * 0.8) # Try to save more

    # Ensure bid is at least a reasonable minimum to stay competitive
    if bid < DAILY_SALARY * 0.5:
        bid = DAILY_SALARY * 0.5 

    # Final adjustments
    # Ensure bid does not exceed budget
    final_bid = min(my_budget, bid)
    
    # Ensure bid is positive
    final_bid = max(0.0, final_bid)

    return final_bid
"""
