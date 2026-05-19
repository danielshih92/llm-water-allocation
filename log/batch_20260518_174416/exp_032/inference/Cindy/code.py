# ============================================================
# Experiment: exp_032
# Agent: Cindy
# Source: exp_032
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_supply = day_context['supply']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid strategy based on daily salary
    base_bid = DAILY_SALARY * 0.5

    # Adjust bid based on my HP (prioritizing survival)
    if my_hp <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.75
    elif my_hp <= 6: # Moderate HP
        base_bid = DAILY_SALARY * 0.6
    else: # Good HP
        base_bid = DAILY_SALARY * 0.4

    # Adjust bid based on supply (perceived scarcity/abundance)
    # My water_req is 13, supply is 15-25. Always enough for one agent.
    # Supply level influences overall bidding aggressiveness.
    supply_factor = 1.0
    if current_supply < 18: # Perceived scarcity, bid slightly higher
        supply_factor = 1.1
    elif current_supply > 22: # Perceived abundance, bid slightly lower
        supply_factor = 0.9

    base_bid *= supply_factor

    # Adjust bid based on opponent's previous bids (if available from previous_trace)
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were aggressive yesterday, react based on my HP
        if highest_prev_bid >= DAILY_SALARY * 0.7: 
            if my_hp <= 4: # I also need water, bid slightly above
                base_bid = max(base_bid, highest_prev_bid + 5)
            else: # Can afford to be less aggressive if HP is good
                base_bid = max(base_bid, highest_prev_bid * 0.9)
        elif highest_prev_bid >= DAILY_SALARY * 0.4:
            if my_hp <= 6:
                base_bid = max(base_bid, highest_prev_bid + 2)
            else:
                base_bid = max(base_bid, highest_prev_bid * 0.95)

    # Final checks for critical situations (end of game, very low budget)
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_hp <= 3: # Last days, need water desperately
        base_bid = DAILY_SALARY * 0.99 # Bid almost everything
    elif my_budget < DAILY_SALARY * 0.5 and my_hp <= 4: # Low budget, need water
        base_bid = DAILY_SALARY * 0.8

    # Ensure bid is within budget and non-negative
    final_bid = min(my_budget, max(0.0, base_bid))

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

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to get water
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Analyze yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Calculate average and max bids from yesterday
    avg_opp_bid_yesterday = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0
    max_opp_bid_yesterday = max(yesterday_bids) if yesterday_bids else 0

    # Base bid strategy
    base_bid = DAILY_SALARY * 0.7

    # Adjust bid based on my HP and no_water_days
    if my_hp <= 2 or my_no_water_days > 0: 
        base_bid = DAILY_SALARY * 0.95 
    elif my_hp <= 5: 
        base_bid = DAILY_SALARY * 0.85 

    # Adjust bid based on day in the episode (late game pressure)
    if current_day >= EPISODE_DAYS * 0.7: 
        base_bid = max(base_bid, DAILY_SALARY * 0.9) 

    # Adjust bid based on opponent's previous bids
    if max_opp_bid_yesterday > 0:
        # If opponents bid high, match or slightly exceed, especially if supply is tight
        if current_supply < (num_alive_opponents + 1) * WATER_REQ * 1.2: 
             base_bid = max(base_bid, max_opp_bid_yesterday * 1.05) 
        else: 
             base_bid = max(base_bid, avg_opp_bid_yesterday * 1.1) 

    # Ensure bid doesn't exceed budget
    final_bid = min(my_budget, base_bid)

    # Ensure a minimum bid to actually get water if I really need it
    if my_hp <= 2 or my_no_water_days > 0:
        final_bid = max(final_bid, DAILY_SALARY * 0.9) 

    # If I have a lot of budget and healthy, and supply is abundant, I can be more conservative
    if my_hp > 7 and my_budget > DAILY_SALARY * 5 and current_supply > (num_alive_opponents + 1) * WATER_REQ * 1.5:
        final_bid = min(final_bid, DAILY_SALARY * 0.6) 

    # Ensure bid is at least 0
    return max(0.0, final_bid)
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

    # Base bid: aim to get water, but don't overspend if not critical
    # This aligns with Bob's average bid from the previous meta-round.
    bid_amount = DAILY_SALARY * 0.5

    # Check previous bids from opponents, especially Bob.
    highest_prev_bid = 0.0
    bob_prev_bid = 0.0

    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                current_prev_bid = prev['bid']
                highest_prev_bid = max(highest_prev_bid, current_prev_bid)
                if opp_id == "Bob":
                    bob_prev_bid = current_prev_bid

    # Strategy: React to high bids from strong opponents, especially Bob.
    if bob_prev_bid > 0 and bob_prev_bid > DAILY_SALARY * 0.5:
        # If Bob is bidding aggressively, match/exceed if my HP is not high
        if my_status['hp'] <= 7: # If HP is getting low or moderate
            bid_amount = max(bid_amount, bob_prev_bid + 1.5)
        else: # If HP is healthy, don't necessarily chase Bob's high bid
            bid_amount = max(bid_amount, DAILY_SALARY * 0.6) # Still competitive but not over-aggressive
    elif highest_prev_bid > 0 and highest_prev_bid > DAILY_SALARY * 0.6:
        # If other opponents bid high, but not as high as Bob usually, react moderately
        if my_status['hp'] <= 5: # If HP is low
            bid_amount = max(bid_amount, highest_prev_bid + 1.0)
        else:
            bid_amount = min(bid_amount, DAILY_SALARY * 0.7) # Cap if healthy

    # Adjust bid based on my HP (critical override)
    if my_status['hp'] <= 2: # Very critical HP
        bid_amount = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP
        bid_amount = max(bid_amount, DAILY_SALARY * 0.8) # Ensure it's at least this high

    # Adjust bid based on remaining days (end game pressure)
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 3 and my_status['hp'] < 6: # End game, need to survive
        bid_amount = max(bid_amount, DAILY_SALARY * 0.9)

    # Ensure bid does not exceed available budget
    final_bid = min(my_status['budget'], bid_amount)

    # Ensure a minimum bid if budget allows, to at least participate
    if final_bid == 0 and my_status['budget'] > 0:
        final_bid = 1.0

    return max(0.0, final_bid)
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
    num_alive_opponents = len(alive_opponents)

    # If I'm the last one, bid minimum to win
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Calculate max previous bid from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_prev_opp_bid = 0
    if yesterday_bids:
        max_prev_opp_bid = max(yesterday_bids)

    # Base bid strategy:
    # Aggressive bid to ensure survival when HP is low
    if my_status['hp'] <= 2:
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        bid = DAILY_SALARY * 0.7
    else:
        # Normal HP, can be strategic
        base_strategic_bid = DAILY_SALARY * 0.3 # 45

        if max_prev_opp_bid > 0:
            # Bid slightly above the max previous bid, but with a floor and ceiling.
            # Ensure a minimum bid to stay competitive, then add a margin to max_prev_opp_bid.
            bid = max(base_strategic_bid * 0.5, max_prev_opp_bid + 5.0)

            # Cap the bid for normal HP to avoid overspending against aggressive opponents.
            bid = min(bid, DAILY_SALARY * 0.6) # Max 90 for normal HP
        else:
            # No previous bids from alive opponents (e.g., Day 1 of the meta-round).
            # Use a moderate base bid.
            bid = base_strategic_bid

    # Ensure bid is always positive and within budget
    bid = max(1.0, bid)
    bid = min(my_status['budget'], bid)

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
        # If no opponents, bid low to save budget
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            # Only consider valid bids, not 0.0 if they failed to bid or died
            if prev['bid'] > 0:
                yesterday_bids.append(prev['bid'])

    # Decision logic based on yesterday's highest pressure and my HP
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If opponents were bidding very high (high pressure)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # If I have good HP, I can afford to risk losing to save budget
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            # If HP is low, bid very aggressively to survive
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        
        # Normal pressure: bid slightly above the highest previous bid, with a floor
        return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))

    # If no yesterday_bids (e.g., first day, or all opponents didn't bid/died)
    if my_status['hp'] <= 2: # Critical HP, bid aggressively
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    # Otherwise, bid moderately
    return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Base bid if no strong pressure or for initial days
    base_bid = DAILY_SALARY * 0.55 

    # If no active opponents, bid conservatively to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_bid = base_bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # Aggressive bidding if previous bids were very high, indicating fierce competition.
        # Threshold (0.65) is set slightly above observed max bids of Alex and Eric (~0.61 of my salary).
        if highest_prev_bid >= DAILY_SALARY * 0.65: # 97.5
            if my_status['hp'] > 3: # Healthy, can afford to be conservative and let opponents pay more
                current_bid = DAILY_SALARY * 0.4 # 60
            else: # Low HP, need water desperately
                current_bid = DAILY_SALARY * 0.9 # 135
        else: # Previous bids were moderate, try to outbid slightly
            current_bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 2.0) # 75 or highest_prev_bid + 2
    
    # Override if HP is critically low, ensuring survival at almost any cost
    if my_status['hp'] <= 2:
        current_bid = DAILY_SALARY * 0.95 # 142.5

    # Ensure bid does not exceed available budget
    return min(my_status['budget'], current_bid)
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
    else:
        highest_prev_bid = DAILY_SALARY * 0.55

    # 1. Critical HP / No Water Days: Bid very aggressively to survive
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        return min(my_status['budget'], DAILY_SALARY * 0.98)

    # 2. React to high opponent bids
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if my_status['hp'] > 3:
            return min(my_status['budget'], max(DAILY_SALARY * 0.6, highest_prev_bid * 0.95))
        else:
            return min(my_status['budget'], highest_prev_bid + 5)

    # 3. General Competitive Bidding: Bid slightly above the highest previous bid
    if highest_prev_bid > 0:
        return min(my_status['budget'], max(DAILY_SALARY * 0.55, highest_prev_bid + 2))

    # 4. Default / Early Game Bidding, adjusted by supply scarcity
    current_supply = day_context['supply']
    if current_supply <= (MIN_SUPPLY + MAX_SUPPLY) / 2:
        return min(my_status['budget'], DAILY_SALARY * 0.7)
    else:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid_amount = 0.0

    is_critical_hp = my_status['hp'] <= 3
    is_late_game_desperation = day_context['day'] >= 8 and my_status['hp'] <= 5

    if is_critical_hp or is_late_game_desperation:
        bid_amount = DAILY_SALARY + 10.0 # Aggressively bid above salary, reacting to Alex's max bid
    else:
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            if highest_prev_bid >= DAILY_SALARY * 0.95: # Opponents very aggressive, conserve budget
                bid_amount = DAILY_SALARY * 0.4
            else:
                # Bid competitively, slightly above previous high or a solid base
                bid_amount = max(DAILY_SALARY * 0.7, highest_prev_bid + 5.0)
        else:
            # No previous bids, bid moderately high to establish presence in a competitive scenario
            bid_amount = DAILY_SALARY * 0.8

    return min(my_status['budget'], bid_amount)
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

    # 1. Critical Survival Condition: If HP is very low or I've missed water, bid aggressively.
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # 2. No Opponents: If no active opponents, bid minimally to secure water.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # 3. Analyze Opponent Bids from Yesterday
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0
    avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0

    # 4. Adaptive Bidding based on Yesterday's Competition and Current State
    # High competition scenario (e.g., Alex/Bob's typical bids)
    if max_yesterday_bid >= DAILY_SALARY * 0.8: # Max bid was > 80% of salary
        if my_status['hp'] > 5: # Have some HP buffer
            return min(my_status['budget'], DAILY_SALARY * 0.75) # High but not maximum
        else: # HP is getting lower, need to be more aggressive
            return min(my_status['budget'], DAILY_SALARY * 0.88)

    # Moderate competition scenario
    elif max_yesterday_bid >= DAILY_SALARY * 0.5: # Max bid was > 50% of salary
        # Bid slightly above average to win, but not excessively
        return min(my_status['budget'], max(DAILY_SALARY * 0.6, avg_yesterday_bid + 5))

    # Low competition or no significant yesterday bids
    else:
        base_bid = DAILY_SALARY * 0.55 # Default moderate bid

        # Adjust based on supply: If supply is tight relative to demand
        num_can_get_water = int(day_context['supply'] / WATER_REQ)
        if num_can_get_water < len(alive_opponents) + 1: # Fewer slots than total agents
            base_bid = max(base_bid, DAILY_SALARY * 0.65) # Increase bid for scarcity
        else:
            base_bid = DAILY_SALARY * 0.5 # Can be more conservative if supply is ample

        # Adjust based on remaining days: Be more aggressive near the end
        remaining_days = EPISODE_DAYS - day_context['day']
        if remaining_days <= 3: 
            base_bid = max(base_bid, DAILY_SALARY * 0.7)

        return min(my_status['budget'], base_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents are alive, bid a minimal amount to secure water.
    if not alive_opponents:
        return max(1.0, min(my_status['budget'], DAILY_SALARY * 0.1))
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    # Base bid: Start with a competitive bid, slightly above average of strong opponents
    # Alex/David average 115-125, which is ~0.77-0.83 of 150
    current_bid = DAILY_SALARY * 0.85 # Aims to be competitive with Alex/David's average-to-max range
    
    # Critical adjustment for low HP: Bid very high to survive
    if my_status['hp'] <= 3:
        current_bid = DAILY_SALARY * 0.98 # Almost full salary
    elif my_status['hp'] <= 6:
        current_bid = DAILY_SALARY * 0.90 # High bid
        
    # Adjustment based on supply scarcity
    # Estimate total water needed by all active players
    total_active_water_req = WATER_REQ # My requirement
    num_active_players = 1
    for opp in alive_opponents:
        total_active_water_req += opp['water_requirement']
        num_active_players += 1
        
    # If supply is very low compared to demand, increase bid
    if total_active_water_req > 0 and day_context['supply'] < total_active_water_req:
        scarcity_ratio = day_context['supply'] / total_active_water_req
        if scarcity_ratio < 0.5: # Very scarce
            current_bid *= 1.15 # Increase by 15%
        elif scarcity_ratio < 0.75: # Moderately scarce
            current_bid *= 1.05 # Increase by 5%
            
    # Adjust bid based on yesterday's highest bid from opponents
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest previous bid was very high, we must match or slightly exceed to stay competitive
        if highest_prev_bid >= DAILY_SALARY * 0.9: # Opponent bid near max
            current_bid = max(current_bid, highest_prev_bid + 2.0) # Slightly outbid
        elif highest_prev_bid >= DAILY_SALARY * 0.75: # Opponent bid moderately high
            current_bid = max(current_bid, highest_prev_bid + 1.0) # Slightly outbid
        
    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], current_bid)
    
    # Ensure bid is at least 1.0 (or a very small positive number)
    return max(1.0, final_bid)
"""
