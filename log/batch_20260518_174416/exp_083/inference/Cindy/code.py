# ============================================================
# Experiment: exp_083
# Agent: Cindy
# Source: exp_083
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    current_supply = day_context['supply']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    total_water_needed = WATER_REQ
    for opp in alive_opponents:
        total_water_needed += opp['water_requirement']

    # --- Base Bid --- 
    bid = DAILY_SALARY * 0.55

    # --- Adjust based on My HP (High Priority) ---
    if my_status['hp'] <= 2: # Critical HP, must get water
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4: # Low HP, need water urgently
        bid = max(bid, DAILY_SALARY * 0.75)

    # --- Adjust based on Opponent's Previous Trace ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents are bidding aggressively
            if my_status['hp'] <= 5: # If my HP is not great, I must be aggressive too
                bid = max(bid, highest_prev_bid + 1.0)
            else: # Healthy, can try to conserve but still compete
                bid = max(bid, highest_prev_bid * 0.95)
        elif highest_prev_bid <= DAILY_SALARY * 0.4: # Opponents are bidding low
            if current_supply >= total_water_needed: # If supply is abundant, I can be conservative
                bid = min(bid, highest_prev_bid * 1.1)
            else: # Supply is tight, or I need water, so bid more definitively
                bid = max(bid, highest_prev_bid * 1.3)
        else: # Moderate opponent bids
            bid = max(bid, highest_prev_bid + 0.5)

    # --- Adjust based on Supply Scarcity ---
    if current_supply < total_water_needed:
        scarcity_factor = (total_water_needed / current_supply)
        bid = max(bid, bid * min(scarcity_factor * 0.8, 1.2))
    elif current_supply >= total_water_needed + WATER_REQ: # Abundant supply
        bid = min(bid, DAILY_SALARY * 0.4)

    # --- End Game Aggression ---
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 3: 
        if my_status['hp'] <= remaining_days * 2: 
            bid = max(bid, DAILY_SALARY * 0.85)

    # --- Final Bid Calculation ---
    final_bid = min(my_status['budget'], max(0.0, bid))
    final_bid = round(final_bid, 2)

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
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.55

    if my_hp <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_no_water_days > 0:
        base_bid = DAILY_SALARY * 0.85
    elif my_hp <= 4:
        base_bid = DAILY_SALARY * 0.75

    if current_supply < WATER_REQ * 2 and num_alive_opponents > 0:
        base_bid *= 1.15
    elif current_supply >= WATER_REQ * 2 and num_alive_opponents > 0:
        base_bid *= 0.9

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.7:
            base_bid = max(base_bid, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.4:
            base_bid = max(base_bid, highest_prev_bid + 1)

    days_left = EPISODE_DAYS - current_day
    if days_left <= 2:
        if my_hp <= 3:
            base_bid = DAILY_SALARY * 1.0
        elif my_budget > DAILY_SALARY * 2:
            base_bid = max(base_bid, DAILY_SALARY * 0.8)

    final_bid = min(my_budget, base_bid)

    if final_bid <= 0 and my_budget > 0:
        final_bid = min(my_budget, 1.0)

    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid a safe low amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # Determine my base bid strategy based on my HP and water needs
    my_base_bid = DAILY_SALARY * 0.55 # Default conservative bid
    if my_status['no_water_days'] >= 1: # Very urgent, haven't gotten water recently
        my_base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 2: # Critical HP
        my_base_bid = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 4: # Low HP
        my_base_bid = DAILY_SALARY * 0.75

    bid = my_base_bid # Initialize bid with my base strategy

    # React to yesterday's opponent bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If opponents are bidding very high (e.g., >= 85% of my daily salary)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # My HP is good, can afford to retreat or try to save budget
                potential_winners = int(day_context['supply'] // WATER_REQ)
                if potential_winners <= num_alive_opponents: # Supply is tight, still need to compete somewhat
                    bid = DAILY_SALARY * 0.7
                else: # Supply is more abundant, try to save more
                    bid = DAILY_SALARY * 0.3
            else: # My HP is low, must compete aggressively to survive
                bid = DAILY_SALARY * 0.95
        else:
            # Opponents not bidding super high, try to outbid them slightly or use my base bid
            potential_winners = int(day_context['supply'] // WATER_REQ)
            if potential_winners <= num_alive_opponents: # Tight supply, need to be competitive
                bid = max(my_base_bid, highest_prev_bid + 5.0)
            else: # More relaxed supply, can try to save or just outbid slightly
                bid = max(my_base_bid * 0.8, highest_prev_bid + 1.5)
    
    # Ensure bid does not exceed budget and is not negative
    final_bid = min(my_status['budget'], bid)
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10 # From meta-round state

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    # Initialize bid with a conservative value
    bid = DAILY_SALARY * 0.6

    # Identify serious opponents (Alex, Bob) and their previous bids
    serious_opponents_yesterday_bids = []
    for opp_id, opp_data in opponents_status.items():
        # Only consider Alex and Bob if they are alive and have a trace
        if opp_id in ["Alex", "Bob"] and opp_data['alive']:
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                serious_opponents_yesterday_bids.append(prev_trace['bid'])

    max_serious_opp_bid = 0
    if serious_opponents_yesterday_bids:
        max_serious_opp_bid = max(serious_opponents_yesterday_bids)

    # --- Bidding logic based on urgency and opponent behavior ---

    # Critical HP or consecutive no-water days
    if my_hp <= 2 or my_status['no_water_days'] >= 1:
        bid = DAILY_SALARY * 0.95 # Bid very high to survive
        if max_serious_opp_bid > 0:
            bid = max(bid, max_serious_opp_bid + 5) # Try to outbid top competitor

    # Adjust for supply scarcity
    # If supply is low (e.g., 15-17), competition is high
    elif current_supply <= WATER_REQ + 4: # Supply up to 17, very tight for two agents
        bid = DAILY_SALARY * 0.75 # Increase base bid
        if max_serious_opp_bid > 0:
            bid = max(bid, max_serious_opp_bid + 2) # Try to slightly outbid

    # If supply is abundant (e.g., 24-25), less competition
    elif current_supply >= WATER_REQ * 2 - 2: # Supply 24 or 25, enough for two
        bid = DAILY_SALARY * 0.55 # Decrease base bid
        if max_serious_opp_bid > 0:
            # If opponents are still bidding high, don't drop too much
            bid = max(bid, max_serious_opp_bid * 0.9)
            if max_serious_opp_bid < DAILY_SALARY * 0.6: # If opponents are low, I can be lower
                bid = min(bid, max_serious_opp_bid + 1) # Just above them

    # Default case: moderate supply, moderate HP
    else:
        if max_serious_opp_bid > 0:
            # If opponents bid high, match/slightly beat
            if max_serious_opp_bid >= DAILY_SALARY * 0.7:
                bid = max(bid, max_serious_opp_bid + 1)
            else: # Otherwise, just slightly above their average
                bid = max(bid, max_serious_opp_bid + 0.5)
        # Ensure a reasonable floor
        bid = max(bid, DAILY_SALARY * 0.5)

    # End-game strategy: be more aggressive in the last few days
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 3: # Last 3 days
        if my_hp <= 3: # Desperate in end game
            bid = max(bid, DAILY_SALARY * 0.98)
            if max_serious_opp_bid > 0:
                bid = max(bid, max_serious_opp_bid + 10)
        elif my_hp <= 5: # Not desperate but need water
            bid = max(bid, DAILY_SALARY * 0.85)
            if max_serious_opp_bid > 0:
                bid = max(bid, max_serious_opp_bid + 5)
        else: # Comfortable but still want to secure water
            bid = max(bid, DAILY_SALARY * 0.7)

    # Final adjustments
    bid = min(bid, my_budget) # Cannot bid more than budget
    bid = max(bid, 0.0) # Bid must be non-negative

    # If I'm desperate, ensure I bid at least 1 (or a small amount) to participate
    if (my_hp <= 2 or my_status['no_water_days'] >= 1) and my_budget > 0:
        bid = max(bid, 1.0)
    elif my_budget == 0: # If no budget, bid 0
        bid = 0.0

    return bid
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

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    bid = 0.0

    if my_status['hp'] <= 2:
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        bid = max(DAILY_SALARY * 0.8, highest_prev_bid + 10)
    else:
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            bid = min(DAILY_SALARY * 0.85, highest_prev_bid + 5)
        else:
            bid = max(DAILY_SALARY * 0.55, highest_prev_bid + 5)
            
    if day_context['supply'] <= 17 and my_status['hp'] < 5:
        bid = max(bid, DAILY_SALARY * 0.8)

    if day_context['day'] == EPISODE_DAYS and my_status['hp'] <= 5:
        bid = my_status['budget']

    final_bid = min(my_status['budget'], bid)
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    LOW_HP_THRESHOLD = 2
    CRITICAL_NO_WATER_DAYS = 1
    BASE_BID_MULTIPLIER = 0.75
    HIGH_COMPETITION_MULTIPLIER = 0.95
    INCREMENT_OVER_OPPONENT = 5.0
    SAFE_BID_MULTIPLIER = 0.4

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * SAFE_BID_MULTIPLIER)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    my_current_bid = 0.0

    if my_status['hp'] <= LOW_HP_THRESHOLD or my_status['no_water_days'] >= CRITICAL_NO_WATER_DAYS:
        my_current_bid = DAILY_SALARY * HIGH_COMPETITION_MULTIPLIER
    elif yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.8:
            my_current_bid = highest_prev_bid + INCREMENT_OVER_OPPONENT
            my_current_bid = min(my_current_bid, DAILY_SALARY * HIGH_COMPETITION_MULTIPLIER)
        else:
            my_current_bid = max(DAILY_SALARY * BASE_BID_MULTIPLIER, average_prev_bid + INCREMENT_OVER_OPPONENT)
    else:
        my_current_bid = DAILY_SALARY * BASE_BID_MULTIPLIER

    my_current_bid = max(0.0, min(my_status['budget'], my_current_bid))

    return my_current_bid
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
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], 1.0)

    # In this scenario, supply (15-25) and WATER_REQ (13) means only one player
    # can get their full water requirement (int(supply / 13) is always 1).
    # This implies a winner-take-all situation for getting 13 water.

    base_bid = DAILY_SALARY * 0.95

    current_day = day_context['day']
    remaining_days = EPISODE_DAYS - current_day

    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        base_bid = DAILY_SALARY * 1.1
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 1.05
    elif remaining_days <= 2:
        base_bid = DAILY_SALARY * 1.1
    elif my_status['hp'] > 6 and my_status['budget'] > DAILY_SALARY * 3:
        base_bid = DAILY_SALARY * 0.85

    highest_opponent_prev_bid = 0.0
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                highest_opponent_prev_bid = max(highest_opponent_prev_bid, prev['bid'])
    
    competitive_bid = base_bid
    if highest_opponent_prev_bid > 0:
        competitive_bid = max(competitive_bid, highest_opponent_prev_bid + 2.0)
    
    competitive_bid = max(competitive_bid, DAILY_SALARY * 0.7)

    final_bid = min(my_status['budget'], competitive_bid)

    if current_day == EPISODE_DAYS:
        final_bid = my_status['budget']
    
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    desperate_for_water = my_status['no_water_days'] >= 2
    urgent_need_for_water = my_status['no_water_days'] == 1

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    remaining_days = EPISODE_DAYS - day_context['day'] + 1

    if desperate_for_water:
        return min(my_status['budget'], DAILY_SALARY * 0.99)
    elif urgent_need_for_water:
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            return min(my_status['budget'], max(DAILY_SALARY * 0.7, highest_prev_bid + 5.0))
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.8)
    else:
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            if highest_prev_bid >= DAILY_SALARY * 0.8:
                if remaining_days > 0 and my_status['budget'] / remaining_days < DAILY_SALARY * 0.7:
                    return min(my_status['budget'], DAILY_SALARY * 0.75)
                else:
                    return min(my_status['budget'], DAILY_SALARY * 0.4)
            else:
                return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 2.0))
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.6)
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

    # If no opponents left, bid minimum to secure water and save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Calculate days remaining (useful for end-game)
    days_remaining = EPISODE_DAYS - day_context['day']

    # --- Aggressive Bidding when in danger ---
    # If HP is very low (2 or less) or I missed water yesterday, bid aggressively
    # Missing water means no_water_days > 0
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # --- Analyze yesterday's bids from active opponents ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Default bid if no previous bids or initial days
    base_bid = DAILY_SALARY * 0.55 # Moderate bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If highest bid was very high, react accordingly
        if highest_prev_bid >= DAILY_SALARY * 0.85: # High pressure from opponents
            if my_status['hp'] > 3: # If HP is good, try to conserve or slightly outbid
                base_bid = min(my_status['budget'], DAILY_SALARY * 0.3) # Conserve
            else: # My HP is not good, I need water, bid high
                base_bid = min(my_status['budget'], DAILY_SALARY * 0.95)
        else: # Opponents bid moderately or low yesterday
            # Try to outbid by a small margin, or keep a competitive bid
            base_bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 2.0)

    # Adjust bid for end-game if I have a good budget and don't need to conserve for future days
    if days_remaining <= 1: # Last day or second to last day
        if my_status['hp'] > 1 and my_status['budget'] > base_bid: # If I'm not dying and have budget
            # Bid aggressively to maximize utility if I have a lot of budget left
            if my_status['hp'] > 2: # If relatively safe, can bid high but not all
                base_bid = min(my_status['budget'], DAILY_SALARY * 0.8)
            else: # Need water urgently
                base_bid = min(my_status['budget'], DAILY_SALARY * 0.95)

    # Final check to ensure bid is within budget and non-negative
    final_bid = min(my_status['budget'], max(0.0, base_bid))

    # Ensure bid is at least a small amount if budget allows, to participate
    if final_bid < 1.0 and my_status['budget'] >= 1.0:
        final_bid = 1.0

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If I'm the only one left, bid minimally to survive
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    current_day = day_context['day']
    current_supply = day_context['supply']

    # Base bid: a fraction of daily salary to stay competitive
    base_bid = DAILY_SALARY * 0.85 # Start competitive, 85% of salary (127.5)

    # Adjustment for my HP and no_water_days
    if my_status['hp'] <= 2: # Critical HP, must get water
        base_bid = DAILY_SALARY * 1.1 # Bid very aggressively (165)
    elif my_status['no_water_days'] > 0: # Missed water yesterday, need to secure it today
        base_bid = DAILY_SALARY * 1.0 # Bid aggressively (150)
    elif my_status['hp'] >= 8 and current_day < EPISODE_DAYS / 2: # Healthy and early/mid game, can be slightly less aggressive
        base_bid = DAILY_SALARY * 0.75 # (112.5)

    # Adjustment for supply scarcity
    # Calculate a supply pressure factor: higher when supply is low
    supply_pressure_factor = 1.0
    # Check if total demand (my_water_req + sum of opponents' water_req) exceeds current supply
    total_water_demand = WATER_REQ + sum(o['water_requirement'] for o in alive_opponents)
    if current_supply < total_water_demand: 
        # The lower the supply, the higher the factor. Max increase 20%
        # Factor ranges from 1.0 (at MAX_SUPPLY) to 1.2 (at MIN_SUPPLY)
        supply_pressure_factor = 1.0 + (1 - (current_supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)) * 0.2
    # Apply supply pressure factor
    base_bid *= supply_pressure_factor

    # Adjustment based on opponent's previous day bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If the highest bid was very competitive, react to it
        if highest_prev_bid >= DAILY_SALARY * 0.9: # If highest opponent bid was 90% of my salary or more
            if my_status['hp'] <= 3: # If I'm vulnerable, try to beat it
                base_bid = max(base_bid, highest_prev_bid + 5) # Bid slightly above
            else: # Otherwise, match or slightly exceed to stay competitive
                base_bid = max(base_bid, highest_prev_bid + 1)
        elif highest_prev_bid < DAILY_SALARY * 0.7: # If opponents bid relatively low
            # Still ensure I get water, maybe slightly above their low bid
            base_bid = max(base_bid, highest_prev_bid * 1.05) # Bid 5% higher than their low bid
            # But don't go too low if supply is tight
            if current_supply < total_water_demand:
                 base_bid = max(base_bid, DAILY_SALARY * 0.7) # Ensure a minimum competitive bid
    
    # Adjustment for late game
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        base_bid *= 1.1 # Increase bid by 10%
        if my_status['hp'] <= 3: # If critical in endgame
            base_bid = max(base_bid, my_status['budget']) # Bid all if needed

    # Final bid constraints
    final_bid = min(my_status['budget'], base_bid)
    
    # Ensure bid is positive
    final_bid = max(final_bid, 0.01)

    # Cap the bid to prevent excessive spending if not critical
    # Opponents max bids were around 220. My salary 150. A cap around 1.5x salary seems reasonable.
    if my_status['hp'] > 2: # If not in critical HP
        final_bid = min(final_bid, DAILY_SALARY * 1.5) # Cap at 225

    # On the very last day, bid everything if necessary to survive
    if current_day == EPISODE_DAYS:
        return my_status['budget']

    return final_bid
"""
