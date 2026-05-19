# ============================================================
# Experiment: exp_119
# Agent: Cindy
# Source: exp_119
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

    # If no opponents, bid minimally to save budget, but ensure water
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    # Critical HP: Bid aggressively to survive
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_supply = day_context['supply']
    
    # Estimate total demand (simplified: everyone needs their water_requirement)
    estimated_total_demand = WATER_REQ + sum(o['water_requirement'] for o in alive_opponents)

    # Determine supply pressure factor
    supply_pressure_factor = 1.0 # Default to moderate
    if current_supply < estimated_total_demand: # Supply deficit
        supply_pressure_factor = 1.2 # Increase bid pressure
        if current_supply < estimated_total_demand * 0.6: # Severe deficit
            supply_pressure_factor = 1.5
    elif current_supply >= estimated_total_demand * 1.2: # Supply surplus
        supply_pressure_factor = 0.8 # Decrease bid pressure

    # Base bid (e.g., a fraction of daily salary)
    base_bid = DAILY_SALARY * 0.55 # Moderate bid

    # Adjust base bid based on HP
    if my_status['hp'] <= 4: # Moderate HP, need water more
        base_bid = DAILY_SALARY * 0.7
    
    # Apply supply pressure factor
    base_bid *= supply_pressure_factor
    
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)
        
        # Adjust bid based on opponent's previous behavior
        if highest_prev_bid > DAILY_SALARY * 0.7: # Opponents were bidding high
            if my_status['hp'] > 4:
                base_bid = max(base_bid, avg_prev_bid * 1.05) 
            else: # If my HP is moderate/low, I must be more aggressive
                base_bid = max(base_bid, highest_prev_bid + 5)
        elif highest_prev_bid < DAILY_SALARY * 0.4: # Opponents were bidding low
             base_bid = min(base_bid, avg_prev_bid * 1.1) 
        else: # Moderate previous bids
            base_bid = max(base_bid, avg_prev_bid * 1.02) 

    # Ensure bid is within budget and reasonable limits
    final_bid = min(my_status['budget'], max(DAILY_SALARY * 0.2, base_bid))

    # Final check for critical HP, overriding other logic if necessary (redundant but safe)
    if my_status['hp'] <= 2:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.95)

    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents are alive, bid minimum to win.
    if num_alive_opponents == 0:
        return min(my_status['budget'], 1)

    # Get yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid
    base_bid = DAILY_SALARY * 0.5 # Default to 75

    # Adjust based on my HP and no_water_days
    if my_status['no_water_days'] > 0: # I lost HP yesterday
        base_bid = DAILY_SALARY * 0.9 # Bid very aggressively
    elif my_status['hp'] <= 3: # Critical HP
        base_bid = DAILY_SALARY * 0.95 # Bid extremely aggressively
    elif my_status['hp'] <= 5: # Low HP
        base_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] >= 8 and my_status['budget'] > DAILY_SALARY * 2: # Good HP, good budget
        base_bid = DAILY_SALARY * 0.6 # Can afford to be slightly less aggressive

    # Adjust based on opponent's previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents bid very high, I need to match or exceed
        if highest_prev_bid >= DAILY_SALARY * 0.85: # Opponents are bidding very high (e.g., Bob/Eric max bids)
            base_bid = max(base_bid, highest_prev_bid + 5) # Try to outbid significantly
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # Opponents bidding moderately high
            base_bid = max(base_bid, highest_prev_bid + 2)
        else: # Opponents bidding low, but I still need to win
             if my_status['hp'] >= 8: # If I have high HP, I can try to win slightly above highest_prev_bid
                 base_bid = max(base_bid, highest_prev_bid + 1)
             else: # If HP is not great, still need to ensure win
                 base_bid = max(base_bid, highest_prev_bid + 3) # Ensure higher bid

    # Consider the current day and remaining days for end-game aggression
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: # Last few days, go all out if needed
        if my_status['hp'] <= 5: # Critical to survive
            base_bid = max(base_bid, DAILY_SALARY * 0.98) # Almost full salary
        elif my_status['hp'] <= 8 and my_status['budget'] < DAILY_SALARY * 2: # Need to secure win
            base_bid = max(base_bid, DAILY_SALARY * 0.9)

    # Ensure bid doesn't exceed budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure bid is at least 1 if budget allows, to avoid 0 bids (unless budget is 0)
    if final_bid == 0 and my_status['budget'] > 0:
        final_bid = 1

    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    # Agent Constants
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From the meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents are alive, bid low to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Collect yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bidding strategy
    # If HP is critically low, bid very aggressively for survival
    if my_status['hp'] <= 2:
        # Must get water, bid near maximum salary
        bid_amount = DAILY_SALARY * 0.95
    # If HP is low but not critical, bid high
    elif my_status['hp'] <= 4:
        bid_amount = DAILY_SALARY * 0.85
    # If HP is good, start with a competitive bid
    else:
        bid_amount = DAILY_SALARY * 0.7

    # Adjust bid based on opponents' previous day behavior
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were bidding very high, competition is fierce
        if highest_prev_bid >= DAILY_SALARY * 0.8: # e.g., 120.0
            if my_status['hp'] <= 4: # If my HP is low, I need to outbid them strongly
                bid_amount = max(bid_amount, highest_prev_bid + 5)
            else: # If my HP is good, be competitive but don't overspend recklessly
                bid_amount = max(bid_amount, highest_prev_bid + 2)
        # If opponents were bidding moderately or low
        else:
            # Try to outbid slightly, but maintain a reasonable floor
            bid_amount = max(bid_amount, highest_prev_bid + 1)
            bid_amount = max(bid_amount, DAILY_SALARY * 0.6) # Ensure bid is at least 90.0

    else:
        # If no yesterday's bids (e.g., Day 1 or all previous opponents died)
        # Use a default competitive bid based on HP
        if my_status['hp'] <= 2:
            bid_amount = DAILY_SALARY * 0.9
        else:
            bid_amount = DAILY_SALARY * 0.75

    # Further adjustments based on supply and number of opponents
    # If supply is very scarce for multiple agents (e.g., only enough for 1 agent or slightly more)
    if day_context['supply'] < WATER_REQ * 1.5 and num_alive_opponents >= 1: # e.g., supply < 19.5
        if my_status['hp'] <= 5: # If HP is a concern, be more aggressive
            bid_amount = max(bid_amount, DAILY_SALARY * 0.9)
        else: # If HP is okay, still be aggressive but save a bit
            bid_amount = max(bid_amount, DAILY_SALARY * 0.8)

    # If it's late in the episode and I have good HP and budget, be more aggressive to secure win
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] > 5 and my_status['budget'] > DAILY_SALARY * 2:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.95)

    # Ensure the bid does not exceed the available budget
    final_bid = min(my_status['budget'], bid_amount)
    # Ensure the bid is not negative
    final_bid = max(0.0, final_bid)

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
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], 1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None and prev_trace.get('status') != 'error':
            yesterday_bids.append(prev_trace['bid'])

    # Default highest_prev_bid for Day 1 or if no valid bids yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else (DAILY_SALARY * 0.5)

    remaining_days = EPISODE_DAYS - day_context['day']

    base_bid = DAILY_SALARY * 0.6 # Default moderate bid

    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        # Critical state: Bid very aggressively to survive
        if remaining_days <= 2:
            base_bid = DAILY_SALARY * 1.2 # Even higher late game
        else:
            base_bid = DAILY_SALARY * 1.05
        
        final_bid = max(base_bid, highest_prev_bid + 10) # Aggressive increment
    elif my_status['hp'] <= 5:
        # Low HP: Bid aggressively
        base_bid = DAILY_SALARY * 0.9
        final_bid = max(base_bid, highest_prev_bid + 5) # Moderate increment
    else:
        # Good HP: More strategic bidding
        # Check if supply is tight (not enough for me + a significant portion of opponents)
        # This heuristic tries to estimate if competition will be high.
        estimated_total_demand = WATER_REQ + sum([o['water_requirement'] for o in alive_opponents])
        
        # If supply is less than what everyone needs, competition is high.
        # Or if supply is barely enough for me and one other agent.
        if day_context['supply'] < estimated_total_demand / 2 or day_context['supply'] < WATER_REQ * 1.5:
            # Supply is tight, bid higher
            base_bid = DAILY_SALARY * 0.8
            final_bid = max(base_bid, highest_prev_bid + 2)
        else:
            # Supply is relatively abundant, can be more conservative
            base_bid = DAILY_SALARY * 0.7
            # If yesterday's bids were low, try to stay just above them
            if highest_prev_bid < DAILY_SALARY * 0.6:
                final_bid = max(base_bid, highest_prev_bid + 1)
            else:
                final_bid = max(base_bid, highest_prev_bid + 1) # Still aim to win if yesterday was high

    # Ensure bid never exceeds current budget and is at least 1
    return max(1, min(my_status['budget'], final_bid))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_HP = 10 # Assuming standard max HP is 10

    current_budget = my_status['budget']

    # --- Base bid strategy --- 
    # Default bid: a moderate fraction of daily salary
    base_bid = DAILY_SALARY * 0.6

    # Adjust bid based on own HP
    if my_status['hp'] <= 2: # Critical HP, bid very aggressively
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP, bid aggressively
        base_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] >= MAX_HP: # Full HP, can afford to be more conservative
        base_bid = DAILY_SALARY * 0.45

    # --- Opponent reaction based on yesterday's bids --- 
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents bid high yesterday, we might need to increase our bid
        # especially if our HP is not full, or supply is tight
        if highest_prev_bid > DAILY_SALARY * 0.7: # High competition detected
            if my_status['hp'] < MAX_HP: # Not at full health, need to win
                base_bid = max(base_bid, highest_prev_bid * 1.05) # Try to outbid slightly
            else: # Full HP, still react but less aggressively to conserve budget
                base_bid = max(base_bid, highest_prev_bid * 0.9)
        elif highest_prev_bid < DAILY_SALARY * 0.4: # Opponents bid low, try to conserve
            if my_status['hp'] >= MAX_HP: # Full health, can risk lower bid
                base_bid = min(base_bid, highest_prev_bid * 1.1)
            else: # Not full health, still aim to win if possible
                base_bid = max(base_bid, highest_prev_bid * 1.05)

    # --- Supply scarcity adjustment --- 
    supply = day_context['supply']
    # If supply is very low (only enough for one agent or less than two agents' requirements)
    if supply <= WATER_REQ + 5: # Tight supply, increase bid pressure
        base_bid = base_bid * 1.15
    elif supply >= WATER_REQ * 2: # Ample supply, can be slightly less aggressive
        base_bid = base_bid * 0.9

    # Final bid must be positive and not exceed current budget
    final_bid = max(1.0, min(base_bid, current_budget))

    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    DAYS_IN_EPISODE = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # My value for water is at least my daily salary, as not getting it means losing HP.
    # Since only one player can get water, competition is fierce.
    my_water_value = DAILY_SALARY

    bid = 0.0

    # If I'm low on HP or have missed water, I must prioritize survival at a high cost.
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        # Bid very aggressively, potentially slightly above daily salary to secure water.
        bid = min(my_status['budget'], DAILY_SALARY * 1.1 + 5.0)
    else:
        # Healthy state, try to be strategic but still aim to win the single water unit.
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            # Bid slightly above the highest previous bid, but ensure a strong floor.
            # This prevents being outbid cheaply and conserves budget if opponents bid low.
            bid = min(my_status['budget'], max(my_water_value * 0.7, highest_prev_bid + 5.0))
        else:
            # No previous bids from active opponents (e.g., first day or all opponents reset).
            # Bid a solid amount to establish presence and win the water.
            bid = min(my_status['budget'], my_water_value * 0.8)

    # Ensure the bid is non-negative.
    return max(0.0, bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # --- Base Bid Strategy ---
    # Start with a moderate bid
    bid = DAILY_SALARY * 0.5

    # Adjust based on my health and water status
    if my_status['no_water_days'] > 0:
        # Critical: Missed water yesterday. Bid very aggressively.
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 2:
        # Near death. Bid extremely aggressively.
        bid = DAILY_SALARY * 0.98
    elif my_status['hp'] <= 5:
        # Low HP. Bid aggressively.
        bid = DAILY_SALARY * 0.85
    elif current_day >= EPISODE_DAYS - 2: # Last 2 days
        # End game, ensure survival
        bid = DAILY_SALARY * 0.9
    elif current_day > EPISODE_DAYS / 2: # Mid to late game
        # If healthy, still be a bit more cautious, but ensure water
        bid = DAILY_SALARY * 0.7
    else:
        # Early game, relatively healthy
        bid = DAILY_SALARY * 0.6

    # --- Opponent Reaction Strategy ---
    highest_prev_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])

    # React to aggressive opponents
    if highest_prev_bid > DAILY_SALARY * 0.7: # If an opponent bid significantly high yesterday
        if my_status['hp'] <= 5: # If I'm struggling, I must try to outbid
            bid = max(bid, highest_prev_bid + 2.0)
        else: # If I'm healthy, I can still try to outbid, but don't overspend too much
            bid = max(bid, highest_prev_bid + 1.0)
    elif highest_prev_bid > 0 and num_alive_opponents > 1:
        # If there's competition and someone bid, ensure I'm competitive
        # Especially if supply is tight for multiple players
        if current_supply < WATER_REQ * num_alive_opponents:
             bid = max(bid, highest_prev_bid + 1.0)
        else: # Supply is not extremely tight, can be slightly less aggressive
             bid = max(bid, highest_prev_bid * 0.95) # Try to get water cheaper if possible

    # --- Supply-based Adjustment ---
    # If supply is very low (e.g., only enough for one player or less than my req)
    if current_supply < WATER_REQ:
        bid = max(bid, DAILY_SALARY * 0.99) # Bid almost everything to get water
    elif current_supply < WATER_REQ * 2 and num_alive_opponents > 1:
        # If supply is tight for two players, ensure I'm competitive
        bid = max(bid, DAILY_SALARY * 0.8)

    # --- Final Bid Constraints ---
    # Ensure bid doesn't exceed available budget
    final_bid = min(my_status['budget'], bid)

    # Ensure bid is at least a minimal amount if budget allows, to participate
    if final_bid <= 0 and my_status['budget'] > 0:
        final_bid = 0.01 # Minimal bid to participate if budget is extremely low or calculated bid was 0
    elif final_bid < 0: # Defensive, should not happen
        final_bid = 0.0

    # If I'm the only one left, bid minimally to save budget
    if num_alive_opponents == 0:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.1)

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)
    num_alive_agents = num_alive_opponents + 1 # Including myself

    # If no opponents are alive, bid just enough to secure water cheaply
    if not alive_opponents:
        return max(1.0, min(my_status['budget'], DAILY_SALARY * 0.1))

    # Calculate total water demand for all alive agents (including myself)
    total_water_demand = WATER_REQ
    for opp in alive_opponents:
        total_water_demand += opp['water_requirement']

    # Get yesterday's bids for analysis, specifically Eric's
    eric_prev_bid = 0.0
    highest_prev_bid_among_all_opps = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid_among_all_opps = max(highest_prev_bid_among_all_opps, prev['bid'])
            if opp['agent_id'] == 'Eric':
                eric_prev_bid = prev['bid']

    # --- Base Bid Strategy ---
    # Start with a moderate bid
    current_bid = DAILY_SALARY * 0.6

    # --- Adjust bid based on my status ---
    # Critical HP: Must win water
    if my_status['hp'] <= 2:
        current_bid = DAILY_SALARY * 0.95
    # Missed water yesterday: Need to secure it today
    elif my_status['no_water_days'] > 0:
        current_bid = DAILY_SALARY * 0.9
    # Low HP late in the game
    elif my_status['hp'] <= 4 and day_context['day'] >= int(EPISODE_DAYS * 0.7):
        current_bid = DAILY_SALARY * 0.85
    # Moderate HP, but supply is very tight
    elif day_context['supply'] < WATER_REQ * num_alive_agents and my_status['hp'] <= 6:
        current_bid = max(current_bid, DAILY_SALARY * 0.75)

    # --- Adjust bid based on market conditions (supply scarcity) ---
    # If supply is less than total demand, competition is high
    if day_context['supply'] < total_water_demand:
        # If supply is very scarce, making it hard for even one agent to get water
        # Heuristic: if supply is less than 1.5 times my water requirement, it's very tight
        if day_context['supply'] < WATER_REQ * 1.5:
             current_bid = max(current_bid, DAILY_SALARY * 0.8)
        # If supply is just generally scarce
        else:
             current_bid = max(current_bid, DAILY_SALARY * 0.7)
    # If supply is abundant, try to save money
    elif day_context['supply'] >= total_water_demand + WATER_REQ * (num_alive_agents - 1):
        current_bid = min(current_bid, DAILY_SALARY * 0.4)

    # --- Adjust bid based on Eric's previous behavior ---
    # Eric is the main strong opponent.
    if eric_prev_bid > 0:
        # If Eric bid high yesterday, we need to counter
        if eric_prev_bid >= DAILY_SALARY * 0.8:
            current_bid = max(current_bid, eric_prev_bid + 5)
        elif eric_prev_bid >= DAILY_SALARY * 0.5:
            current_bid = max(current_bid, eric_prev_bid + 2)
    # Also consider highest bid from any opponent, not just Eric, if Eric didn't bid high.
    elif highest_prev_bid_among_all_opps > 0:
        if highest_prev_bid_among_all_opps >= DAILY_SALARY * 0.7:
             current_bid = max(current_bid, highest_prev_bid_among_all_opps + 3)

    # --- Final Bid Constraints ---
    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], current_bid)

    # Ensure bid is not excessively high (e.g., more than daily salary plus a small buffer)
    final_bid = min(final_bid, DAILY_SALARY + 10)

    # Ensure a non-zero bid if budget allows
    if final_bid <= 0.0:
        return 0.1

    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From Current Meta-Round State

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid a minimal amount to secure water and save budget.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine highest bid from yesterday
    # If no bids, assume a moderate baseline
    highest_prev_bid = DAILY_SALARY * 0.5
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # --- Bidding Strategy ---

    # Critical HP: If very low HP, bid aggressively to survive.
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # Check if supply is tight. WATER_REQ is 13.
    # If supply is 15, only one agent can get full water. If 25, two agents.
    # Tight if supply is less than or equal to 1.5 times my requirement, implying limited water for multiple agents.
    is_supply_tight = day_context['supply'] <= WATER_REQ * 1.5

    bid = 0.0
    # If high competition from yesterday
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # If my HP is good and supply isn't too tight, try to save a bit but still be competitive.
        if my_status['hp'] > 5 and not is_supply_tight:
            bid = DAILY_SALARY * 0.7 # Slightly lower than aggressive opponents
        else:
            bid = highest_prev_bid + 2.0 # Slightly outbid them
    elif highest_prev_bid >= DAILY_SALARY * 0.6:
        # Moderate competition
        bid = highest_prev_bid + 1.5
    else:
        # Low competition or default baseline
        bid = DAILY_SALARY * 0.6 # Base bid

    # Adjust bid upwards if supply is tight to increase chances of winning.
    if is_supply_tight and bid < DAILY_SALARY * 0.75:
        bid = max(bid, DAILY_SALARY * 0.75) # Increase aggression if supply is tight

    # Ensure bid is not more than budget
    final_bid = min(my_status['budget'], bid)
    
    # Ensure bid is at least a minimal amount to be considered, unless truly out of budget.
    if final_bid <= 0.01 and my_status['budget'] > 0:
        final_bid = max(0.1, final_bid)
    elif final_bid <= 0.01 and my_status['budget'] <= 0: # If budget is 0, bid 0
        final_bid = 0.0

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
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return 1

    high_pressure = (my_hp <= 2) or (my_no_water_days > 0)

    yesterday_bids = []
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive'] and opp_data.get('previous_trace') and opp_data['previous_trace'].get('bid') is not None:
            yesterday_bids.append(opp_data['previous_trace']['bid'])

    target_bid = 0

    if high_pressure:
        target_bid = DAILY_SALARY * 0.95
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            target_bid = max(target_bid, highest_prev_bid + 5)
    else:
        base_bid = DAILY_SALARY * 0.6
        target_bid = base_bid

        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            if highest_prev_bid >= DAILY_SALARY * 0.8:
                target_bid = max(target_bid, highest_prev_bid + 2)
            else:
                target_bid = max(target_bid, highest_prev_bid + 1)

    target_bid = max(1, target_bid)
    target_bid = min(target_bid, my_budget)

    return target_bid
"""
