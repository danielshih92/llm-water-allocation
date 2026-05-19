# ============================================================
# Experiment: exp_034
# Agent: Cindy
# Source: exp_034
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

    current_supply = day_context['supply']

    # --- Bidding Strategy --- 

    # 1. Critical HP: Survival is paramount
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # 2. Low HP: Need water, but not critically
    if my_status['hp'] <= 4:
        # If supply is very low, competition is high, bid higher
        # Estimate total water needed if everyone gets their requirement
        total_req_estimate = WATER_REQ * (num_alive_opponents + 1)
        if current_supply < total_req_estimate * 0.8:
            return min(my_status['budget'], DAILY_SALARY * 0.8)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.7)

    # 3. Healthy HP (my_status['hp'] > 4)
    if not alive_opponents:
        # No opponents, bid minimally to secure water
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # Exploit aggressive opponents if I am healthy
        if highest_prev_bid >= DAILY_SALARY * 0.85: # Opponents bid very high
            # I am healthy, let them overpay if they are desperate
            # Bid moderately low to conserve budget, unless supply is critically low.
            if current_supply < WATER_REQ: # Supply is less than my own requirement, super competitive
                return min(my_status['budget'], DAILY_SALARY * 0.9) # Still need to fight for water
            return min(my_status['budget'], DAILY_SALARY * 0.3) # Conserve budget

        # Opponents were not extremely aggressive, react to supply and their bids
        total_req_estimate = WATER_REQ * (num_alive_opponents + 1)

        if current_supply < total_req_estimate * 0.8: # Supply is tight relative to total demand
            # Bid slightly above their highest to secure water, but not excessively
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 5))
        else: # Supply is ample or moderately competitive
            # Bid moderately, slightly above average or a base amount
            return min(my_status['budget'], max(DAILY_SALARY * 0.4, highest_prev_bid * 0.9)) # Try to undercut slightly or bid base 40%

    else:
        # No previous bids (e.g., Day 1 or all previous opponents died)
        # Bid based on supply and number of opponents
        total_req_estimate = WATER_REQ * (num_alive_opponents + 1)
        if current_supply < total_req_estimate * 0.8: # Supply is tight
            return min(my_status['budget'], DAILY_SALARY * 0.6) # Bid moderately high
        else: # Ample supply
            return min(my_status['budget'], DAILY_SALARY * 0.4) # Bid moderately

    # Fallback default bid (should ideally not be reached)
    return min(my_status['budget'], DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])
            
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            else:
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else:
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
    
    return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    # 1. Base bid - a moderate amount
    bid = DAILY_SALARY * 0.5

    # 2. Health-based adjustment for self
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        # Critical health or missed water yesterday, bid aggressively
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] >= 8:
        # Healthy, can afford to bid lower
        bid = DAILY_SALARY * 0.4

    # 3. Opponent Analysis (using previous_trace)
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    opponent_danger_bids = [] # Bids from opponents who were low HP or no water days yesterday

    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])
            # Use hp_after from previous_trace to gauge their yesterday's health
            # Use status from previous_trace to check if they got water
            if prev_trace.get('status') == 'no_water' or prev_trace.get('hp_after', 10) <= 2:
                opponent_danger_bids.append(prev_trace['bid'])
    
    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0
    max_danger_bid = max(opponent_danger_bids) if opponent_danger_bids else 0

    # Adjust bid based on opponent behavior
    if max_danger_bid > bid:
        # If any opponent was desperate and bid high, I might need to match or slightly exceed
        bid = max_danger_bid + (DAILY_SALARY * 0.05) # Add 5% of salary
    elif max_yesterday_bid > bid and my_status['hp'] <= 5:
        # If general competition was high and I'm not very healthy
        bid = max_yesterday_bid + (DAILY_SALARY * 0.02) # Add 2% of salary
    elif my_status['hp'] >= 8 and max_yesterday_bid > DAILY_SALARY * 0.7:
        # If I'm healthy and others are bidding high, try to undercut slightly but still competitive
        bid = max(bid, DAILY_SALARY * 0.6) # Ensure a reasonable bid, but don't overbid

    # 4. Supply/Demand Adjustment
    total_water_demand = WATER_REQ
    active_players_count = 1 # Myself
    for opp in alive_opponents:
        total_water_demand += opp['water_requirement']
        active_players_count += 1

    # Avoid division by zero if no demand (shouldn't happen with at least one player)
    supply_ratio = day_context['supply'] / total_water_demand if total_water_demand > 0 else 1.0

    if supply_ratio < 0.8: # Supply is low relative to demand, competition is high
        bid *= 1.1 # Increase bid by 10%
    elif supply_ratio > 1.5: # Supply is high relative to demand, competition is low
        bid *= 0.9 # Decrease bid by 10%

    # 5. Budget and final constraints
    # Ensure bid doesn't exceed current budget
    bid = min(bid, my_status['budget'])

    # Ensure bid is at least a minimum to stay in the game (avoid 0 bids unless no budget)
    bid = max(bid, DAILY_SALARY * 0.1 if my_status['budget'] > 0 else 0)

    # Cap bid to prevent overspending unless absolutely critical
    # If I'm critical (hp <= 2 or no_water_days > 0), I can go higher, up to my budget
    if not (my_status['hp'] <= 2 or my_status['no_water_days'] > 0):
        bid = min(bid, DAILY_SALARY * 1.05) # Cap at 105% of daily salary if not desperate
    
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

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Default bid (base for healthy state)
    bid = DAILY_SALARY * 0.55

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Strategy based on my HP
    if my_current_hp <= 1:
        # Critical: Must get water at almost any cost
        bid = DAILY_SALARY * 0.99
    elif my_current_hp == 2:
        # Very low: High priority to get water
        bid = DAILY_SALARY * 0.9
    elif my_current_hp == 3:
        # Low: Need water, but can be slightly less aggressive than critical
        bid = DAILY_SALARY * 0.8
    else:
        # Healthy HP: Can be more strategic, react to opponents and supply
        if highest_prev_bid > DAILY_SALARY * 0.7:
            # Opponents are aggressive, respond competitively
            bid = max(bid, highest_prev_bid + 1.0)
            bid = min(bid, DAILY_SALARY * 0.85) # Cap to avoid overpaying too much
        elif highest_prev_bid > 0:
            # Opponents bid, but not extremely high. Bid slightly above to secure water.
            bid = max(bid, highest_prev_bid + 5.0)
            bid = min(bid, DAILY_SALARY * 0.7) # Cap it
        # If highest_prev_bid is 0, stick to base_bid or adjusted by other factors

    # Adjust for end game (last 2 days)
    if current_day >= EPISODE_DAYS - 2:
        if my_current_hp < 5: # If not very healthy, push harder
            bid = max(bid, DAILY_SALARY * 0.95)
        else: # If healthy, still be competitive to win or maintain lead
            bid = max(bid, DAILY_SALARY * 0.8)

    # Adjust for supply scarcity if many agents are alive
    # Consider my own water requirement as well
    needed_water_slots = num_alive_opponents + 1
    if current_supply < needed_water_slots * WATER_REQ * 0.75: # Supply is tight
        if my_current_hp < 4:
            bid = max(bid, DAILY_SALARY * 0.9)
        else:
            bid = max(bid, DAILY_SALARY * 0.75)

    # Final constraints
    # Ensure bid does not exceed current budget
    bid = min(bid, my_current_budget)
    
    # Ensure a minimum bid if I need water and have budget
    if bid < DAILY_SALARY * 0.1 and my_current_budget > 0 and my_current_hp > 0:
        bid = max(bid, DAILY_SALARY * 0.15) # Bid at least something if I'm alive and have money

    # Ensure bid is at least 1 if budget allows, to actually make a bid
    if bid < 1.0 and my_current_budget >= 1.0:
        bid = 1.0
    elif bid < 1.0 and my_current_budget < 1.0: # If budget is less than 1, bid whatever is left
        bid = my_current_budget

    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQ = 13
    MY_DAILY_SALARY = 150
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        # No opponents, bid minimum to save budget
        return min(my_status['budget'], MY_DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    base_bid = 0.0

    # Prioritize survival when HP is critical or consecutive no-water days
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        # Must win. Bid very aggressively, ensuring to outbid previous highest.
        base_bid = MY_DAILY_SALARY * 0.95
        if highest_prev_bid > 0:
            base_bid = max(base_bid, highest_prev_bid + 5) # Bid a bit higher to secure win

    elif my_status['hp'] <= 5:
        # Risky state: Strong need for water. Be aggressive but consider budget.
        # If opponents are extremely aggressive and my budget is low, might save for next day.
        if my_status['budget'] < MY_DAILY_SALARY * 0.8 and highest_prev_bid > MY_DAILY_SALARY * 0.8:
            base_bid = MY_DAILY_SALARY * 0.3 # Temporarily back off if budget is low and competition is fierce
        else:
            base_bid = MY_DAILY_SALARY * 0.75
            if highest_prev_bid > 0:
                base_bid = max(base_bid, highest_prev_bid + 3)

    else: # Normal HP
        # Good HP, can afford to be strategic.
        # If opponents are overbidding significantly, consider saving budget.
        if highest_prev_bid > MY_DAILY_SALARY * 0.8 and my_status['hp'] > 7:
            base_bid = MY_DAILY_SALARY * 0.3 # Let others fight, save budget
        else:
            # Normal competitive bid, adjusted by day progression
            if day_context['day'] < int(EPISODE_DAYS / 2):
                # Early game: slightly more conservative
                base_bid = MY_DAILY_SALARY * 0.5
                if highest_prev_bid > 0:
                    base_bid = max(base_bid, highest_prev_bid + 1)
            else:
                # Late game: competition might intensify, or some opponents might be weak.
                base_bid = MY_DAILY_SALARY * 0.6
                if highest_prev_bid > 0:
                    base_bid = max(base_bid, highest_prev_bid + 2)

    # Ensure bid does not exceed budget and is non-negative
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
    MIN_BID = 1.0

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_competitors = len(alive_opponents)

    # If no opponents, bid minimally to save budget.
    if num_competitors == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Calculate available water slots
    water_slots = int(day_context['supply'] // WATER_REQ)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid based on HP
    # If HP is critical, we must get water
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    # If HP is low, still prioritize getting water
    elif my_status['hp'] <= 4:
        base_bid_hp = DAILY_SALARY * 0.8
    # If HP is moderate, balance survival and budget
    elif my_status['hp'] <= 7:
        base_bid_hp = DAILY_SALARY * 0.6
    # If HP is high, can afford to be more aggressive with budget saving
    else:
        base_bid_hp = DAILY_SALARY * 0.4

    # Adjust bid based on yesterday's bids and competition
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # High competition: water_slots < (num_competitors + 1)
        # This means not everyone can get water.
        if water_slots < (num_competitors + 1):
            # If opponents bid very high yesterday, and my HP is good, I might let them overspend.
            # But if my HP is not great, I need to fight for it.
            if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents are bidding very aggressively
                if my_status['hp'] > 5: # My HP is good, I can risk missing water for a day
                    bid = DAILY_SALARY * 0.3 # Bid low, let them fight
                else: # My HP is not good, I need water
                    bid = max(base_bid_hp, highest_prev_bid + 10) # Aggressively outbid
            else: # Opponents are bidding moderately high
                bid = max(base_bid_hp, highest_prev_bid + 5) # Try to win by a small margin
        else: # Low competition: water_slots >= (num_competitors + 1)
            # Enough water for everyone, try to bid just above highest previous bid or base_bid_hp
            bid = max(base_bid_hp * 0.8, highest_prev_bid + 1)
    else:
        # No previous bids (e.g., Day 1 or all previous bidders died)
        # Default to base_bid_hp, adjusted for supply
        if water_slots < (num_competitors + 1): # Tight supply
            bid = base_bid_hp * 1.1 # Slightly more aggressive
        else: # Abundant supply
            bid = base_bid_hp * 0.9 # Slightly less aggressive

    # Final bid must be at least MIN_BID and not exceed budget
    final_bid = max(MIN_BID, bid)
    return min(my_status['budget'], final_bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid a minimal amount to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    current_day = day_context['day']
    current_supply = day_context['supply']

    # Initialize a base bid
    # Bid increases slightly as days progress to reflect increasing desperation
    # Factor in remaining days: more desperate towards the end
    remaining_days = EPISODE_DAYS - current_day + 1
    # A base bid that slightly increases over time, more aggressively towards the end
    base_bid_factor = 0.4 + (current_day / EPISODE_DAYS) * 0.3
    if remaining_days <= 3: # Last few days, increase base bid significantly
        base_bid_factor += 0.2
    base_bid = DAILY_SALARY * base_bid_factor

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0

    # Determine my bid based on my status and opponent's previous actions
    my_bid = base_bid

    # High desperation: low HP or no water yesterday
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        my_bid = DAILY_SALARY * 0.95
    # Medium desperation: relatively low HP
    elif my_status['hp'] <= 5:
        my_bid = DAILY_SALARY * 0.85 # Slightly more aggressive for medium desperation
    # Low desperation: good HP, but still need to compete
    else:
        # If max opponent bid was high, react to it
        if max_yesterday_bid > DAILY_SALARY * 0.6:
            my_bid = max(my_bid, max_yesterday_bid + 5) # Bid slightly higher than max if it was already high
        elif max_yesterday_bid > 0:
            my_bid = max(my_bid, max_yesterday_bid * 1.1) # Otherwise, bid a bit higher than max

    # Adjust bid based on supply: if supply is low, competition is higher
    # Estimate total water needed for all active players (including self)
    total_water_needed_approx = WATER_REQ * (num_alive_opponents + 1)

    if current_supply < total_water_needed_approx * 0.75: # If supply is significantly lower than demand
        my_bid *= 1.15 # Increase bid due to high competition
    elif current_supply > total_water_needed_approx * 1.25: # If supply is abundant
        my_bid *= 0.9 # Decrease bid

    # Ensure bid does not exceed budget or a reasonable maximum
    my_bid = min(my_status['budget'], my_bid)
    my_bid = max(my_bid, DAILY_SALARY * 0.1) # Ensure a minimum bid to stay in the game
    
    # Ensure bid is not excessively high, cap it at a reasonable level like 1.2 * DAILY_SALARY
    my_bid = min(my_bid, DAILY_SALARY * 1.2)

    return my_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_competitors = len(alive_opponents)

    # Default bid if no specific conditions apply
    base_bid = MY_DAILY_SALARY * 0.85

    # 1. Prioritize survival if HP is critically low
    if my_status['hp'] <= 2:
        return min(my_status['budget'], MY_DAILY_SALARY * 1.1)
    # If HP is low and recently missed water, be more aggressive
    if my_status['hp'] <= 4 and my_status['no_water_days'] > 0:
        return min(my_status['budget'], MY_DAILY_SALARY * 1.05)

    # 2. If no competitors, bid minimum to get water
    if not alive_opponents:
        return min(my_status['budget'], MY_DAILY_SALARY * 0.1)

    # 3. Analyze yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # If no valid yesterday bids from alive opponents, use a default competitive bid
    if not yesterday_bids:
        bid = base_bid
    else:
        highest_prev_bid = max(yesterday_bids)
        
        # Determine total water demand vs supply
        total_water_demand = (num_alive_competitors + 1) * MY_WATER_REQUIREMENT
        
        # Adjust bid based on highest previous bid and supply scarcity
        if current_supply < total_water_demand * 1.1: # Supply is scarce
            if highest_prev_bid >= MY_DAILY_SALARY * 0.9: # Opponents were aggressive
                bid = max(base_bid * 1.1, highest_prev_bid + 5.0) # Bid higher to secure water
            else: # Opponents were not very aggressive despite scarcity
                bid = max(base_bid, highest_prev_bid + 10.0) # Be more aggressive than them
        elif current_supply > total_water_demand * 1.5: # Supply is abundant
            if my_status['hp'] > 5 and my_status['budget'] > MY_DAILY_SALARY * 3: # Can afford to be less aggressive
                bid = min(highest_prev_bid * 0.9, MY_DAILY_SALARY * 0.7) # Try to get it cheaper
            else: # Still need to be somewhat competitive
                bid = max(base_bid * 0.7, highest_prev_bid * 0.95)
        else: # Normal supply
            if highest_prev_bid >= MY_DAILY_SALARY * 0.9: # Opponents were aggressive
                bid = max(base_bid, highest_prev_bid + 2.0) # Try to outbid slightly
            else: # Opponents were moderate
                bid = max(base_bid * 0.9, highest_prev_bid + 1.0) # Be slightly above them

    # Ensure bid is within budget and positive
    final_bid = min(bid, my_status['budget'])
    final_bid = max(1.0, final_bid) # Minimum bid of 1.0

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
    num_active_agents = len(alive_opponents) + 1 # Include myself

    # Calculate available "full water requirement" units
    # CRITICAL INDEX RULE: day_context['supply'] is float, so // results in float. Cast to int for comparison.
    available_water_slots = int(day_context['supply'] // WATER_REQ)

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace')
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # --- Determine base bid based on my urgency and competition ---
    bid_value = DAILY_SALARY * 0.5 # Default moderate bid

    # High urgency: HP is critical or I've missed water previously
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        bid_value = DAILY_SALARY * 0.95 # Bid very high to ensure survival
    elif my_status['hp'] <= 4: # Still urgent
        bid_value = DAILY_SALARY * 0.8

    # Adjust bid based on water scarcity and opponent's previous behavior
    if available_water_slots < num_active_agents: # Water is scarce
        if highest_prev_bid > 0: # If opponents bid yesterday
            # Try to outbid the highest previous bid, but not excessively
            bid_value = max(bid_value, highest_prev_bid + (DAILY_SALARY * 0.05)) # Bid slightly higher than max
        else: # No previous bids, but water is scarce, bid higher than usual
            bid_value = max(bid_value, DAILY_SALARY * 0.75)
    else: # Water is plentiful
        if my_status['hp'] > 4 and my_status['no_water_days'] == 0: # If not urgent, try to conserve
            if highest_prev_bid > 0: # If opponents bid yesterday
                # Bid just above the highest previous bid, but keep it reasonable
                bid_value = min(bid_value, highest_prev_bid + 1.0)
                bid_value = max(bid_value, DAILY_SALARY * 0.3) # Ensure it's not too low
            else: # No previous bids, plentiful water, bid low
                bid_value = DAILY_SALARY * 0.35
        else: # Still somewhat urgent even if water is plentiful
            bid_value = max(bid_value, DAILY_SALARY * 0.6)

    # --- Final Bid Adjustments ---
    # Ensure bid doesn't exceed budget or daily salary (with a small buffer)
    final_bid = min(my_status['budget'], bid_value)
    final_bid = min(final_bid, DAILY_SALARY * 1.05) # Cap bid slightly above salary to avoid irrational bids

    # Ensure bid is at least 1 to participate
    final_bid = max(1.0, final_bid)

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    bid_value = DAILY_SALARY * 0.7

    if my_hp <= 2:
        bid_value = DAILY_SALARY * 1.05
    elif my_hp <= 4:
        bid_value = DAILY_SALARY * 0.9
    elif my_hp >= 8:
        bid_value = DAILY_SALARY * 0.65

    highest_prev_bid = 0
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev_trace['bid'])

    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            bid_value = max(bid_value, highest_prev_bid + (DAILY_SALARY * 0.05))
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            bid_value = max(bid_value, highest_prev_bid + (DAILY_SALARY * 0.02))
        else:
            if my_hp >= 8:
                bid_value = min(bid_value, highest_prev_bid + (DAILY_SALARY * 0.1))
            else:
                bid_value = max(bid_value, DAILY_SALARY * 0.6)

    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2:
        bid_value = max(bid_value, DAILY_SALARY * 0.95)
        if my_hp <= 4:
            bid_value = max(bid_value, DAILY_SALARY * 1.1)

    final_bid = min(my_budget, bid_value)
    final_bid = max(0.01, final_bid)

    return final_bid
"""
