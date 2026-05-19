# ============================================================
# Experiment: exp_076
# Agent: Cindy
# Source: exp_076
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_players = len(alive_opponents) + 1 # Include myself

    # 1. If no opponents, bid very low as water is guaranteed
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # 2. Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0

    # 3. Determine base bid
    current_bid = DAILY_SALARY * 0.5 # Default moderate bid

    # Adjust for HP: If HP is critically low, bid very aggressively
    if my_status['hp'] <= 2:
        current_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # If HP is somewhat low, bid aggressively
        current_bid = DAILY_SALARY * 0.8

    # Adjust for supply scarcity/abundance
    supply = day_context['supply']
    total_water_demand = WATER_REQ * num_alive_players

    if supply < WATER_REQ: # Very scarce: not enough for even one player
        current_bid = max(current_bid, DAILY_SALARY * 0.9)
        if highest_prev_bid > 0:
            current_bid = max(current_bid, highest_prev_bid + 5) # Bid very high to win

    elif supply < total_water_demand: # Scarce: not enough for everyone, but enough for at least one
        current_bid = max(current_bid, DAILY_SALARY * 0.7)
        if highest_prev_bid > 0:
            current_bid = max(current_bid, highest_prev_bid + 2) # Outbid previous high if scarce

    elif supply >= total_water_demand + WATER_REQ: # Abundant: enough for everyone + extra for one more
        current_bid = min(current_bid, DAILY_SALARY * 0.3)
        if highest_prev_bid > 0:
            current_bid = min(current_bid, highest_prev_bid * 0.9) # Try to undercut

    # React to highest previous bid if not in an emergency HP state and supply isn't extremely scarce
    if highest_prev_bid > 0 and my_status['hp'] > 2 and supply >= WATER_REQ:
        if highest_prev_bid >= DAILY_SALARY * 0.85: # Opponent was very aggressive
            if my_status['hp'] > 4 and supply >= total_water_demand: # Can afford to be less aggressive if supply is good and HP is high
                current_bid = min(current_bid, DAILY_SALARY * 0.4)
            else: # Need to compete
                current_bid = max(current_bid, highest_prev_bid + 1.5)
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # Opponent was moderately aggressive
            current_bid = max(current_bid, highest_prev_bid + 1)
        else: # Opponent bid low
            current_bid = max(current_bid, highest_prev_bid * 1.1) # Slightly outbid, but keep it low

    # Ensure bid is within budget and is at least 1
    final_bid = max(1, min(my_status['budget'], current_bid))

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_active_opponents = len(alive_opponents)

    if not alive_opponents:
        if day_context['supply'] >= WATER_REQ:
            return min(my_status['budget'], DAILY_SALARY * 0.1)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.4)

    bid = DAILY_SALARY * 0.5

    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        bid = DAILY_SALARY * 0.75

    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2:
        bid = max(bid, DAILY_SALARY * 0.9)
    elif remaining_days <= 4:
        bid = max(bid, DAILY_SALARY * 0.7)

    if day_context['supply'] < WATER_REQ:
        bid = max(bid, DAILY_SALARY * 0.6)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3 and remaining_days > 2 and day_context['supply'] >= WATER_REQ * (num_active_opponents + 1):
                bid = min(bid, DAILY_SALARY * 0.6)
            else:
                bid = max(bid, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            bid = max(bid, highest_prev_bid + 1)
        else:
            bid = max(bid, highest_prev_bid * 1.1)
            bid = min(bid, DAILY_SALARY * 0.6)

    bid = min(bid, my_status['budget'])
    bid = max(bid, 0.0)

    if (my_status['hp'] <= 2 or my_status['no_water_days'] > 0) and my_status['budget'] > 0:
        bid = max(bid, 1.0)

    if bid == 0.0 and my_status['budget'] > 0 and day_context['supply'] > 0:
        bid = 0.1

    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid minimally to save budget.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine bid based on yesterday's highest bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # Threshold for considering a bid 'very high' based on observed opponent behavior (Bob, Eric)
        HIGH_BID_THRESHOLD = DAILY_SALARY * 0.9 # 135

        if highest_prev_bid >= HIGH_BID_THRESHOLD:
            # Opponents are bidding very high.
            if my_status['hp'] > 3: # If I have good HP
                # Aim to win, potentially slightly above yesterday's high, but at least my salary.
                bid_amount = max(DAILY_SALARY * 1.0, highest_prev_bid + 2.0)
                return min(my_status['budget'], bid_amount)
            else: # If my HP is low (<= 3), I desperately need water.
                # Bid very aggressively, potentially significantly above salary to ensure survival.
                bid_amount = max(DAILY_SALARY * 1.2, highest_prev_bid + 5.0)
                return min(my_status['budget'], bid_amount)
        else:
            # Yesterday's highest bid was not 'very high'.
            # Bid competitively, slightly above yesterday's highest, with a solid base.
            BASE_COMPETITIVE_BID = DAILY_SALARY * 0.75 # 112.5
            bid_amount = max(BASE_COMPETITIVE_BID, highest_prev_bid + 1.5)
            return min(my_status['budget'], bid_amount)

    # Fallback if no yesterday bids (e.g., Day 1 of the episode)
    
    if my_status['hp'] <= 2: # Very low HP
        # Bid very high to secure water on Day 1 or if no history.
        return min(my_status['budget'], DAILY_SALARY * 1.1) # 165
    else: # Healthy HP
        # Bid competitively but save some budget on Day 1 or if no history.
        return min(my_status['budget'], DAILY_SALARY * 0.8) # 120
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

    # If no opponents, bid a minimal amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Initialize bid with a moderate value
    bid = DAILY_SALARY * 0.5

    # Adjust bid based on my current HP
    if my_status['hp'] <= 2:
        bid = DAILY_SALARY * 0.95 # Critical HP, bid very aggressively
    elif my_status['hp'] <= 4:
        bid = DAILY_SALARY * 0.75 # Low HP, bid aggressively
    elif my_status['hp'] <= 6:
        bid = DAILY_SALARY * 0.6 # Medium-low HP, bid moderately high

    # Adjust bid based on supply scarcity relative to demand
    num_active_players = len(alive_opponents) + 1
    
    # Calculate effective supply per player if everyone needs water
    # day_context['supply'] is a float, so division is fine.
    available_supply_per_player = day_context['supply'] / num_active_players

    if available_supply_per_player < WATER_REQ * 1.0: # Supply is less than base requirement per player
        bid = max(bid, DAILY_SALARY * 0.8) # Increase bid significantly due to high competition
    elif available_supply_per_player < WATER_REQ * 1.5: # Supply is somewhat tight
        bid = max(bid, DAILY_SALARY * 0.65) # Increase bid moderately

    # React to the highest bid from yesterday
    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponent was very aggressive
            bid = max(bid, highest_prev_bid + 1.5) # Try to outbid aggressive opponents
        else: # Opponent was moderately aggressive
            bid = max(bid, highest_prev_bid + 0.5) # Slightly outbid

    # Final bid constraints
    bid = max(1.0, bid) # Ensure bid is at least 1.0
    bid = min(bid, my_status['budget']) # Cannot bid more than current budget
    
    # Cap bid to prevent excessive overspending, but allow for aggressive bids.
    bid = min(bid, DAILY_SALARY * 1.15) 

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
    
    bid_value = DAILY_SALARY * 0.5 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return max(1, min(my_status['budget'], DAILY_SALARY * 0.1))

    if my_status['hp'] <= 2:
        bid_value = DAILY_SALARY * 0.98 
    elif my_status['hp'] <= 4:
        bid_value = DAILY_SALARY * 0.85 
    elif my_status['no_water_days'] > 0:
        bid_value = DAILY_SALARY * 0.75 
    else:
        bid_value = DAILY_SALARY * 0.6 

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] <= 4 or my_status['no_water_days'] > 0:
                bid_value = max(bid_value, highest_prev_bid + 5)
            else:
                bid_value = max(bid_value, highest_prev_bid + 1)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            bid_value = max(bid_value, highest_prev_bid + 1)
        elif highest_prev_bid < DAILY_SALARY * 0.3 and my_status['hp'] > 5 and my_status['no_water_days'] == 0:
            bid_value = min(bid_value, DAILY_SALARY * 0.4)

    current_supply = day_context['supply']
    num_possible_winners = int(current_supply // WATER_REQ)

    if num_possible_winners == 1:
        if num_alive_opponents >= 1:
            if my_status['hp'] <= 6 or my_status['no_water_days'] > 0:
                bid_value *= 1.15 
            else:
                bid_value *= 1.05 
    elif num_possible_winners >= 2:
        if my_status['hp'] > 5 and my_status['no_water_days'] == 0:
            bid_value *= 0.9
        else:
            bid_value *= 1.05 

    current_day = day_context['day']
    remaining_days = EPISODE_DAYS - current_day

    if remaining_days <= 3 and my_status['hp'] > 0:
        if my_status['hp'] <= 4 or my_status['no_water_days'] > 0:
            bid_value = max(bid_value, DAILY_SALARY * 0.9) 
        else:
            bid_value = max(bid_value, DAILY_SALARY * 0.7) 

    final_bid = min(my_status['budget'], bid_value)
    
    return max(1, int(final_bid))
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
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    bid = DAILY_SALARY * 0.5

    if my_status['hp'] <= 2:
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        bid = DAILY_SALARY * 0.75
    elif my_status['hp'] >= 7:
        bid = DAILY_SALARY * 0.4

    estimated_total_demand = (num_alive_opponents + 1) * WATER_REQ
    current_supply = day_context['supply']

    if current_supply < estimated_total_demand:
        shortage_factor = (estimated_total_demand - current_supply) / estimated_total_demand
        bid *= (1 + shortage_factor * 0.6)
    elif current_supply >= estimated_total_demand + WATER_REQ * num_alive_opponents:
        bid *= 0.75

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] <= 4:
                bid = max(bid, highest_prev_bid + (DAILY_SALARY * 0.1))
            else:
                bid = max(bid, highest_prev_bid + 5)
        elif average_prev_bid < DAILY_SALARY * 0.4:
            bid = min(bid, average_prev_bid + (DAILY_SALARY * 0.05))

    final_bid = max(1.0, bid)
    final_bid = min(final_bid, my_status['budget'])

    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] <= 3:
        final_bid = min(my_status['budget'], DAILY_SALARY * 1.2)

    return float(final_bid)
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

    # If no opponents are alive, bid low to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.55  # A moderate starting bid (82.5)

    # Adjust bid based on my HP
    if my_status['hp'] <= 2:  # Critical HP
        base_bid = DAILY_SALARY * 0.95  # Bid very aggressively (142.5)
    elif my_status['hp'] <= 4:  # Low HP
        base_bid = DAILY_SALARY * 0.8  # Aggressive bid (120)

    # Adjust bid based on supply scarcity
    # If supply is less than enough for two agents (my_req + another_req), competition is higher
    if day_context['supply'] < WATER_REQ * 2:
        # Only increase if not already critical HP, to avoid overriding ultra-high bids
        if my_status['hp'] > 2:
            base_bid = max(base_bid, DAILY_SALARY * 0.7)  # Ensure a higher bid on scarce days (105)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.85) # Even more aggressive if critical HP and scarce

    # Adjust bid based on opponent's previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest previous bid was very high, and I'm not critical HP, maybe slightly above it
        if highest_prev_bid >= DAILY_SALARY * 0.8:  # If opponents bid >= 120
            if my_status['hp'] > 2:  # If not critical, try to outbid if necessary
                base_bid = max(base_bid, highest_prev_bid + 5)
            else:  # If critical HP, ensure we bid very high to win
                base_bid = max(base_bid, highest_prev_bid + 10)
        # If highest previous bid was moderate, match or slightly exceed to win
        elif highest_prev_bid >= DAILY_SALARY * 0.5:  # If opponents bid >= 75
            base_bid = max(base_bid, highest_prev_bid + 2)
        # If highest previous bid was low, still bid moderately to save budget but win
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.5)  # Ensure at least 75

    # End game strategy: Bid more aggressively towards the end
    if day_context['day'] >= EPISODE_DAYS - 2:  # Last 2 days
        if my_status['hp'] > 0:  # If still alive
            base_bid = max(base_bid, DAILY_SALARY * 0.9)  # Bid very high (135)

    # Ensure bid does not exceed available budget and is not negative
    final_bid = min(my_status['budget'], base_bid)
    
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13
    EPISODE_DAYS = 10

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid strategy
    bid = DAILY_SALARY * 0.5 # Default moderate bid

    # 1. Prioritize survival if HP is low
    if my_hp <= 2:
        bid = DAILY_SALARY * 0.95 # Bid very high to ensure water
    elif my_hp <= 4:
        bid = DAILY_SALARY * 0.8 # High bid

    # 2. Analyze opponent's yesterday's bids and identify Eric
    max_yesterday_bid = 0
    eric_is_alive = False
    for opp in alive_opponents:
        if opp['agent_id'] == 'Eric':
            eric_is_alive = True
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            max_yesterday_bid = max(max_yesterday_bid, prev_trace['bid'])

    # 3. Adjust bid based on supply and competition
    num_agents_who_can_get_water = int(current_supply // WATER_REQ)
    total_potential_competitors = num_alive_opponents + 1 # Me + alive opponents

    if num_agents_who_can_get_water < total_potential_competitors: # Supply is scarce
        # Increase bid due to scarcity
        bid = max(bid, DAILY_SALARY * 0.7)
        if num_agents_who_can_get_water <= 1: # Very scarce
            bid = max(bid, DAILY_SALARY * 0.85)

        # If Eric is alive, he's a strong competitor, especially with scarce supply
        if eric_is_alive:
            bid = max(bid, DAILY_SALARY * 0.9) # Be very aggressive if Eric is a threat and supply is low
            if max_yesterday_bid > DAILY_SALARY * 0.8: # If Eric (or others) bid very high yesterday
                bid = max(bid, max_yesterday_bid + 5) # Try to outbid him

    else: # Supply is abundant or sufficient
        # If supply is very abundant, try to bid lower if not critical
        if current_supply >= total_potential_competitors * WATER_REQ * 1.5:
            if my_hp > 5: # If healthy, try to save money
                bid = min(bid, DAILY_SALARY * 0.3)
            else: # Still need water, but can be less aggressive
                bid = min(bid, DAILY_SALARY * 0.5)
        
        # If Eric is alive, he might still bid high, so don't go too low if he was aggressive yesterday
        if eric_is_alive and max_yesterday_bid > DAILY_SALARY * 0.7:
            bid = max(bid, DAILY_SALARY * 0.6) # Keep a competitive floor

    # 4. React to yesterday's highest bid if I'm not in critical health
    if my_hp > 4 and max_yesterday_bid > DAILY_SALARY * 0.6:
        if num_agents_who_can_get_water < total_potential_competitors: # Still scarce
            bid = max(bid, max_yesterday_bid + 2)
        else: # Abundant, maybe don't react as strongly
            bid = max(bid, max_yesterday_bid * 0.9)

    # 5. End game strategy
    days_remaining = EPISODE_DAYS - current_day
    if days_remaining <= 2: # Last few days
        if my_hp <= 2: # Critical, must survive
            bid = DAILY_SALARY * 0.99
        elif my_hp <= 4: # Low, need water
            bid = max(bid, DAILY_SALARY * 0.8)
        else: # Healthy, try to conserve for final days
            bid = min(bid, DAILY_SALARY * 0.6)

    # 6. If no opponents left, bid minimally
    if not alive_opponents:
        bid = min(my_budget, DAILY_SALARY * 0.1 if my_hp > 5 else DAILY_SALARY * 0.5)
        
    # Ensure bid is at least 1.0 and not more than budget
    final_bid = max(1.0, min(my_budget, bid))

    return float(final_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15.0
    MAX_SUPPLY = 25.0
    EPISODE_DAYS = 10 # From meta-round state, hardcoded for this scenario

    # 1. Base bid calculation
    # A reasonable base bid, competitive enough to secure water without overspending initially.
    base_bid = DAILY_SALARY * 0.5 # 75.0

    # 2. Survival mode: If HP is low or I've missed water recently
    # If HP is low (e.g., 3 or less) or I haven't gotten water for a day, bid aggressively.
    if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1:
        # Bid very aggressively, close to daily salary to ensure survival.
        aggressive_bid = DAILY_SALARY * 0.95 # 142.5
        return max(0.0, min(my_status['budget'], aggressive_bid))

    # 3. Opponent analysis (yesterday's highest bid)
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_bid = base_bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # React to opponent bidding patterns
        if highest_prev_bid >= DAILY_SALARY * 0.75: # If opponents are bidding very high (>= 112.5)
            # If my HP is good, try to be slightly less aggressive to save budget, but still competitive
            if my_status['hp'] > 5:
                current_bid = max(base_bid, highest_prev_bid * 0.9)
            else: # If my HP is moderate, still need to fight hard
                current_bid = max(base_bid, highest_prev_bid + 2.0) # Slightly outbid
        elif highest_prev_bid < DAILY_SALARY * 0.4: # If opponents are bidding very low (< 60.0)
            # Try to win water cheaply, but ensure it's above a minimum competitive level
            current_bid = max(base_bid * 0.8, highest_prev_bid + 2.0) # Bid slightly above to secure
        else: # Moderate bidding by opponents
            # Bid slightly above the highest previous bid to secure water
            current_bid = max(base_bid, highest_prev_bid + 1.5)
    
    # 4. Adjust bid based on supply scarcity
    # Normalize supply to a 0-1 range (0 = min supply, 1 = max supply)
    supply_level = (day_context['supply'] - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if (MAX_SUPPLY - MIN_SUPPLY) > 0 else 0.5

    # If supply is low (supply_level closer to 0), increase bid. If high, decrease.
    # Factor ranges from 1.2 (min supply) to 0.8 (max supply)
    supply_adjustment_factor = 1.2 - (supply_level * 0.4)
    current_bid *= supply_adjustment_factor

    # 5. Adjust bid based on day progress (pressure increases towards end)
    # Scale day from 0 to 1 (day 1 to EPISODE_DAYS)
    day_progress = (day_context['day'] - 1) / (EPISODE_DAYS - 1) if EPISODE_DAYS > 1 else 0.0

    # Increase bid slightly as the game progresses (up to 20% increase by last day)
    day_adjustment_factor = 1.0 + (day_progress * 0.20)
    current_bid *= day_adjustment_factor

    # Ensure bid is at least a minimal amount to be considered serious
    current_bid = max(current_bid, DAILY_SALARY * 0.2) # Minimum bid of 30.0

    # Ensure the bid does not exceed current budget
    final_bid = min(my_status['budget'], current_bid)

    # Ensure bid is positive
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid if no strong signals from yesterday
    # This logic is used if yesterday_bids is empty or as a fallback
    base_bid = DAILY_SALARY * 0.55
    if my_status['hp'] <= 2: # Critical HP, bid aggressively
        base_bid = DAILY_SALARY * 0.9

    bid_value = base_bid # Default to base_bid

    # Adjust bid based on yesterday's highest bid if available
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Check if competition was very high yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.85: # High pressure threshold
            if my_status['hp'] > 3: # My HP is good, try to conserve
                bid_value = DAILY_SALARY * 0.3
            else: # My HP is low, need to win at higher cost
                bid_value = DAILY_SALARY * 0.95
        else: # Moderate competition yesterday
            # Bid slightly above the highest previous bid or a reasonable amount
            bid_value = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)

    # Ensure bid doesn't exceed current budget and is at least 0
    return max(0.0, min(my_status['budget'], bid_value))
"""
