# ============================================================
# Experiment: exp_049
# Agent: Cindy
# Source: exp_049
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    bid = 0.0

    if num_alive_opponents == 0:
        # No opponents, bid minimum to get water
        bid = 1.0
    else:
        # There are opponents, and given the supply range (15-25) vs WATER_REQ (13),
        # competition for water is always high for multiple players.
        if my_no_water_days > 0:
            # Already missed water, very critical, bid very high
            bid = DAILY_SALARY * 0.95
        elif my_hp <= 2:
            # Low HP, critical, bid high
            bid = DAILY_SALARY * 0.9
        elif my_hp <= 3:
            # Medium-low HP, bid quite high
            bid = DAILY_SALARY * 0.85
        else:
            # Good HP, but still competitive environment. Aim to win but save some money.
            bid = DAILY_SALARY * 0.75

    # Ensure bid does not exceed budget and is at least 1
    final_bid = max(1.0, min(bid, float(my_budget)))

    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    current_day = day_context['day']

    alive_opponents = [o for o o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        return max(0.0, min(my_current_budget, DAILY_SALARY * 0.4))

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid
    base_bid = DAILY_SALARY * 0.75 # Default competitive bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest previous bid was very aggressive
        if highest_prev_bid >= DAILY_SALARY * 0.9: # e.g., >= 135
            if my_current_hp <= 2: # Very low HP, must get water
                base_bid = DAILY_SALARY * 0.98 # 147
            elif my_current_hp <= 5: # Low HP
                base_bid = DAILY_SALARY * 0.9 # 135
            else: # Healthy HP, try to outbid but conserve
                base_bid = max(DAILY_SALARY * 0.8, highest_prev_bid + 2) # min 120, slightly above
        # If highest previous bid was moderately aggressive
        elif highest_prev_bid >= DAILY_SALARY * 0.7: # e.g., >= 105
            if my_current_hp <= 3: # Low HP
                base_bid = DAILY_SALARY * 0.9 # 135
            else: # Healthy HP
                base_bid = max(DAILY_SALARY * 0.75, highest_prev_bid + 1) # min 112.5, slightly above
        # If highest previous bid was low
        else: # highest_prev_bid < 105
            if my_current_hp <= 3: # Low HP
                base_bid = DAILY_SALARY * 0.8 # 120
            else: # Healthy HP, try to outbid but conserve
                base_bid = max(DAILY_SALARY * 0.6, highest_prev_bid + 1) # min 90, slightly above
    else: # No yesterday's bids (e.g., Day 1) or no active bidders yesterday
        if my_current_hp <= 2: # Very low HP
            base_bid = DAILY_SALARY * 0.95 # 142.5
        elif my_current_hp <= 5: # Low HP
            base_bid = DAILY_SALARY * 0.85 # 127.5
        else: # Healthy HP
            base_bid = DAILY_SALARY * 0.75 # 112.5

    # Final adjustments for late game desperation
    if current_day >= EPISODE_DAYS * 0.7 and my_current_hp <= 5: # Last 30% of days, low HP
        base_bid = max(base_bid, DAILY_SALARY * 0.95) # Ensure high bid

    # Ensure bid doesn't exceed current budget and is non-negative
    final_bid = min(my_current_budget, base_bid)
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

    # If no opponents, bid just enough to win and conserve budget.
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    # Critical HP strategy: Bid very high to survive
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # Calculate how many agents can fully satisfy their water requirement
    # CRITICAL INDEX RULE: Ensure int() for division result if used as index. Here, it's for comparison.
    num_full_req_possible = int(day_context['supply']) // WATER_REQ
    
    # Determine if supply is scarce (fewer full requirements than agents + me)
    supply_is_scarce = num_full_req_possible < (num_alive_opponents + 1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # Adjust bid based on opponent's previous aggression and my HP
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents were very aggressive (e.g., bid > 120)
            if my_status['hp'] > 5: # My HP is still good, can risk a slightly lower bid to test
                # Bid competitively, but don't necessarily overbid previous high if I have buffer
                return min(my_status['budget'], max(DAILY_SALARY * 0.6, highest_prev_bid * 0.95))
            else: # My HP is moderate (4 or 5), need to be aggressive
                # Bid to win, slightly above previous high
                return min(my_status['budget'], max(DAILY_SALARY * 0.85, highest_prev_bid + 5))
        else: # Opponents were moderate/low yesterday
            if supply_is_scarce:
                # Bid slightly above highest previous bid to try and win when supply is tight
                return min(my_status['budget'], max(DAILY_SALARY * 0.6, highest_prev_bid + 5))
            else:
                # Supply is abundant, can bid more moderately
                return min(my_status['budget'], DAILY_SALARY * 0.55)
    else: # No yesterday bids (e.g., first day or all opponents are new/dead)
        if supply_is_scarce:
            # Start with a moderately high bid if supply is tight
            return min(my_status['budget'], DAILY_SALARY * 0.7)
        else:
            # Start with a moderate bid
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid: aim for profit, but ensure survival. A bit higher than average Bob/David, lower than Alex/Eric.
    bid = DAILY_SALARY * 0.65 

    # --- Adjustments ---

    # 1. Survival instinct: If HP is low or no water received yesterday
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        bid = DAILY_SALARY * 1.05 # Bid slightly above salary to aggressively secure water
    elif my_status['hp'] <= 4:
        bid = DAILY_SALARY * 0.9 # High bid to prevent critical HP

    # 2. Opponent analysis from yesterday's bids (previous_trace)
    max_opponent_prev_bid = 0
    total_opponent_water_demand = 0
    num_competitors = len(alive_opponents)

    for opp in alive_opponents:
        total_opponent_water_demand += opp['water_requirement']
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            max_opponent_prev_bid = max(max_opponent_prev_bid, prev['bid'])

    # If there are strong previous bids from opponents, react by trying to outbid them slightly
    if max_opponent_prev_bid > DAILY_SALARY * 0.7: 
        bid = max(bid, max_opponent_prev_bid * 1.05)

    # 3. Supply and demand pressure
    total_demand = WATER_REQ + total_opponent_water_demand
    
    # If total demand exceeds current supply, competition is high, bid higher
    if total_demand > current_supply:
        bid = max(bid, DAILY_SALARY * 0.8) 
        if num_competitors > 1: # If multiple competitors and scarcity
            bid = max(bid, DAILY_SALARY * 0.9)

    # If supply is very low (e.g., close to min_supply)
    if current_supply <= MIN_SUPPLY + 2:
        bid = max(bid, DAILY_SALARY * 0.95)

    # If supply is abundant (e.g., close to max_supply) and demand is low
    # And I'm not in critical HP, try to save money
    if current_supply >= MAX_SUPPLY - 2 and total_demand < current_supply and my_status['hp'] > 4:
        bid = min(bid, DAILY_SALARY * 0.5) 

    # 4. End-game strategy (last few days)
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last 2 days, go aggressive for survival
        bid = max(bid, DAILY_SALARY * 1.1)
    elif remaining_days <= 4: # Last 4 days, be more firm
        bid = max(bid, DAILY_SALARY * 0.9)


    # Final checks
    # Ensure bid doesn't exceed budget
    bid = min(bid, my_status['budget'])

    # Ensure bid is at least 1 to participate
    bid = max(1.0, bid)

    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    current_day = day_context['day']
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Prioritize survival if HP is critically low
    if my_hp <= 2:
        return min(my_budget, DAILY_SALARY * 0.98)

    # If HP is low but not critical, still bid high
    if my_hp <= 4:
        return min(my_budget, DAILY_SALARY * 0.85)

    # React to opponent's previous bids if available
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were very aggressive yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_hp > 5 and my_budget > highest_prev_bid + 10:
                return min(my_budget, highest_prev_bid + 5)
            else:
                return min(my_budget, highest_prev_bid * 1.05)
        
        # If opponents were moderately aggressive
        elif highest_prev_bid >= DAILY_SALARY * 0.4:
            return min(my_budget, max(DAILY_SALARY * 0.5, highest_prev_bid + 2))
        
        # If opponents were passive yesterday
        else:
            return min(my_budget, max(DAILY_SALARY * 0.35, highest_prev_bid + 1))
    
    # Default bidding strategy if no previous bids or specific HP conditions met
    # Adjust based on supply and number of active agents
    cindy_water_portions = int(supply / WATER_REQ)
    num_active_agents = len(alive_opponents) + 1

    if cindy_water_portions < num_active_agents:
        return min(my_budget, DAILY_SALARY * 0.7)
    elif cindy_water_portions >= num_active_agents * 1.5:
        return min(my_budget, DAILY_SALARY * 0.4)
    else:
        return min(my_budget, DAILY_SALARY * 0.55)
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
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    base_bid = DAILY_SALARY * 0.7

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    bid = base_bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 5:
                bid = max(base_bid, DAILY_SALARY * 0.75)
            else:
                bid = max(base_bid, DAILY_SALARY * 0.95)
        else:
            bid = max(base_bid, highest_prev_bid + 5.0)
    
    if my_status['hp'] <= 3:
        bid = max(bid, DAILY_SALARY * 0.98)
    elif my_status['hp'] <= 6:
        bid = max(bid, DAILY_SALARY * 0.85)
    
    current_day = day_context['day']
    if current_day >= EPISODE_DAYS - 1:
        bid = max(bid, DAILY_SALARY * 0.99)
    elif current_day >= EPISODE_DAYS - 3:
        bid = max(bid, DAILY_SALARY * 0.95)
    
    final_bid = min(my_status['budget'], bid)
    
    if my_status['budget'] >= DAILY_SALARY * 0.3 and final_bid < DAILY_SALARY * 0.3:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.3)
        
    final_bid = max(0.0, final_bid)

    return final_bid
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

    # If no opponents, bid low to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Look at yesterday's situation (Trace)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid strategy
    base_bid = DAILY_SALARY * 0.5 # Default competitive bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were bidding very high, indicating high competition or desperation
        if highest_prev_bid >= DAILY_SALARY * 0.8: # e.g., >= 120 for Cindy
            # If I'm healthy, I can afford to be less aggressive, let them fight
            if my_status['hp'] > 3: # Assuming initial HP is 5, 3 is still okay
                base_bid = DAILY_SALARY * 0.35 # Bid 52.5
            else: # I'm not healthy, I need water desperately
                base_bid = DAILY_SALARY * 0.95 # Bid 142.5
        else: # Moderate bids yesterday
            # Try to outbid yesterday's highest by a small margin, but at least the base competitive bid
            base_bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 2.0)
    else:
        # No yesterday bids available, use default based on my health
        if my_status['hp'] <= 2: # Very low HP
            base_bid = DAILY_SALARY * 0.9
        elif my_status['no_water_days'] > 0: # Missed water yesterday
            base_bid = DAILY_SALARY * 0.75
        else:
            base_bid = DAILY_SALARY * 0.6 # Slightly higher than default 0.5 to establish presence

    # Adjust bid based on current supply and total expected demand
    total_water_needed = WATER_REQ
    for opp in alive_opponents:
        total_water_needed += opp['water_requirement']

    current_supply = day_context['supply']

    if current_supply < total_water_needed: # Demand exceeds supply, high competition expected
        if my_status['no_water_days'] > 0 or my_status['hp'] <= 3:
            base_bid *= 1.15 # Increase bid by 15% if desperate
        else:
            base_bid *= 1.08 # Slight increase if not desperate but supply is tight
    else: # Supply meets or exceeds demand, lower competition expected
        if my_status['hp'] > 3 and my_status['no_water_days'] == 0:
            base_bid *= 0.9 # Decrease bid by 10% if healthy and not desperate
        else:
            base_bid *= 0.95 # Slight decrease even if not perfectly healthy, as supply is good

    # Adjust for day progression (end game desperation)
    if day_context['day'] >= EPISODE_DAYS - 2: # Last two days
        if my_status['hp'] > 2 and my_status['budget'] >= DAILY_SALARY * 2: # Healthy and good budget
            base_bid = min(my_status['budget'], max(base_bid, DAILY_SALARY * 0.7)) # Ensure a strong bid
        elif my_status['hp'] <= 2: # Desperate
            base_bid = min(my_status['budget'], DAILY_SALARY * 0.99) # Bid almost everything

    # Final bid should not exceed budget and should be positive
    final_bid = min(my_status['budget'], max(0.1, base_bid))

    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    # Filter out opponents who are not alive or are known non-players (like David)
    alive_opponents = [o for o in opponents_status.values() if o['alive'] and o['agent_id'] != 'David']

    # If no real opponents, bid a minimal amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine the highest bid from yesterday. Default to 0 if no bids.
    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Strategy based on my HP and opponent's previous behavior

    # If I'm in critical HP (2 or less), bid very aggressively to survive
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95) # Bid 142.5

    # If the highest previous bid was very high (e.g., Eric's typical high bids)
    # DAILY_SALARY * 0.85 = 150 * 0.85 = 127.5
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # If my HP is good (>3), I can afford to let opponents overpay and conserve budget
        if my_status['hp'] > 3:
            return min(my_status['budget'], DAILY_SALARY * 0.3) # Bid 45
        # If my HP is low (3 or less), I must compete aggressively
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.95) # Bid 142.5

    # Otherwise (highest_prev_bid was moderate or low)
    # Try to win by bidding slightly above the highest previous bid, with a minimum floor.
    # DAILY_SALARY * 0.5 = 150 * 0.5 = 75
    return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta_round_state

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']

    # Identify strong, alive opponents (Alex and Bob based on meta-round context)
    strong_competitor_bids = []
    for agent_id, opp in opponents_status.items():
        if opp['alive'] and agent_id in ["Alex", "Bob"]:
            if opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None:
                strong_competitor_bids.append(opp['previous_trace']['bid'])

    # Base bid strategy: Start with a competitive bid
    base_bid = DAILY_SALARY * 0.55 # A bit above Bob's average, below Alex's average

    if strong_competitor_bids:
        highest_prev_strong_bid = max(strong_competitor_bids)
        
        # Adjust bid to outcompete based on their previous high bids
        if highest_prev_strong_bid >= DAILY_SALARY * 0.6: 
            base_bid = max(base_bid, highest_prev_strong_bid + 5) # Try to outbid by a margin
        elif highest_prev_strong_bid > DAILY_SALARY * 0.4: 
            base_bid = max(base_bid, highest_prev_strong_bid + 2) # Slightly outbid
        else: # They bid low, maintain a strong base
            base_bid = max(base_bid, DAILY_SALARY * 0.5)

    # Urgency adjustment based on my HP
    if my_hp <= 2: # Critical HP
        base_bid = max(base_bid, DAILY_SALARY * 0.95) # Bid very high
    elif my_hp <= 4: # Low HP
        base_bid = max(base_bid, DAILY_SALARY * 0.8) # Bid high
    elif my_hp <= 6: # Medium-low HP
        base_bid = max(base_bid, DAILY_SALARY * 0.7) # Bid moderately high

    # Urgency adjustment based on remaining days (endgame pressure)
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_hp <= 4: # Late game and low HP, must win
        base_bid = max(base_bid, DAILY_SALARY * 0.9) # Ensure a strong bid

    # Ensure bid does not exceed available budget and is not negative
    final_bid = min(my_budget, base_bid)
    
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 

    VERY_AGGRESSIVE_BID_FACTOR = 0.9
    AGGRESSIVE_BID_FACTOR = 0.75
    MODERATE_BID_FACTOR = 0.65
    CONSERVATIVE_BID_FACTOR = 0.5
    LOW_BID_FACTOR = 0.3 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * LOW_BID_FACTOR)

    CRITICAL_HP_THRESHOLD = 2 

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_bid = 0.0

    if my_status['hp'] <= CRITICAL_HP_THRESHOLD:
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            current_bid = max(DAILY_SALARY * AGGRESSIVE_BID_FACTOR, highest_prev_bid + 2.0)
        else:
            current_bid = DAILY_SALARY * VERY_AGGRESSIVE_BID_FACTOR
    else:
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            if highest_prev_bid >= DAILY_SALARY * AGGRESSIVE_BID_FACTOR:
                current_bid = max(DAILY_SALARY * MODERATE_BID_FACTOR, highest_prev_bid + 1.0)
            else:
                current_bid = max(DAILY_SALARY * CONSERVATIVE_BID_FACTOR, highest_prev_bid + 1.0)
        else:
            current_bid = DAILY_SALARY * MODERATE_BID_FACTOR

    current_bid = min(current_bid, my_status['budget'])
    current_bid = max(0.0, current_bid)

    return current_bid
"""
