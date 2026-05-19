# ============================================================
# Experiment: exp_021
# Agent: Cindy
# Source: exp_021
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
    EPISODE_DAYS = 10 # From meta-round state

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Determine the base bid strategy based on my HP
    # Since only one agent can get full water, bidding is highly competitive.
    # The goal is to outbid opponents to secure water, especially when HP is low.

    base_bid = DAILY_SALARY * 0.5 # A default reasonable bid

    if my_hp <= 1: # Critical HP, must get water
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 2: # Low HP
        base_bid = DAILY_SALARY * 0.85
    elif my_hp <= 3: # Moderate HP
        base_bid = DAILY_SALARY * 0.75
    else: # High HP (4 or 5)
        base_bid = DAILY_SALARY * 0.65 # Can afford to be slightly less aggressive

    # React to yesterday's opponent bids
    yesterday_bids = []
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive'] and opp_data.get('previous_trace'):
            prev_bid = opp_data['previous_trace'].get('bid')
            if prev_bid is not None:
                yesterday_bids.append(prev_bid)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents bid high yesterday, I need to bid higher today.
        # Add a small increment to ensure winning, but not too much to waste budget.
        if my_hp <= 2: # If critical, ensure to win by a good margin
            base_bid = max(base_bid, highest_prev_bid + DAILY_SALARY * 0.1) # Bid significantly higher
        else: # Otherwise, try to win with a smaller margin
            base_bid = max(base_bid, highest_prev_bid + 1.0) # Just slightly above

    # Ensure bid doesn't exceed current budget
    final_bid = min(my_budget, base_bid)

    # If it's the last day and I need water, bid everything (or almost) to survive.
    # This is a 10-day game. If day 9 or 10 and I'm at risk, go all in.
    if current_day >= EPISODE_DAYS - 1: # Last two days
        if my_hp <= 3: # If I might die soon, bid very aggressively
            final_bid = min(my_budget, DAILY_SALARY * 0.99)

    # Ensure bid is at least 1 to participate and avoid zero bid issues
    final_bid = max(1.0, final_bid)

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
    MIN_BID_FRACTION = 0.4
    HIGH_BID_FRACTION = 0.95
    CRITICAL_HP = 3
    
    STRONG_BIDDERS_META = ["Alex", "David"]

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * MIN_BID_FRACTION * 0.5)

    yesterday_bids = []
    strong_opponent_yesterday_bids = []
    
    for agent_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
                if agent_id in STRONG_BIDDERS_META:
                    strong_opponent_yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    
    highest_strong_bid = 0
    if strong_opponent_yesterday_bids:
        highest_strong_bid = max(strong_opponent_yesterday_bids)

    current_day = day_context['day']
    remaining_days = EPISODE_DAYS - current_day + 1
    
    base_bid = DAILY_SALARY * MIN_BID_FRACTION

    if my_status['hp'] <= CRITICAL_HP:
        base_bid = DAILY_SALARY * HIGH_BID_FRACTION
        if my_status['hp'] <= 1:
            base_bid = DAILY_SALARY + 10
    elif my_status['hp'] <= CRITICAL_HP + 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.7)

    if remaining_days <= 3:
        base_bid = max(base_bid, DAILY_SALARY * 0.85)
        if my_status['hp'] <= CRITICAL_HP + 1:
             base_bid = max(base_bid, DAILY_SALARY * 0.95)
    elif remaining_days <= 5:
        base_bid = max(base_bid, DAILY_SALARY * 0.6)

    competitive_bid_from_opponents = highest_strong_bid if highest_strong_bid > 0 else highest_prev_bid

    if competitive_bid_from_opponents > 0:
        if competitive_bid_from_opponents >= DAILY_SALARY * 0.8:
            if my_status['hp'] > CRITICAL_HP:
                base_bid = max(base_bid, competitive_bid_from_opponents + 1)
            else:
                base_bid = max(base_bid, competitive_bid_from_opponents + 5)
        else:
            base_bid = max(base_bid, competitive_bid_from_opponents + 1)

    if day_context['supply'] < WATER_REQ * 1.5:
        if len(alive_opponents) >= 1:
            base_bid = max(base_bid, DAILY_SALARY * 0.8)
            if my_status['hp'] <= CRITICAL_HP:
                base_bid = max(base_bid, DAILY_SALARY + 15)

    bid = min(base_bid, my_status['budget'])

    if bid <= 0 and my_status['budget'] > 0:
        bid = min(my_status['budget'], 1.0)
    elif bid <= 0:
        bid = 0.0

    return bid
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

    if num_alive_opponents == 0:
        return min(my_status['budget'], 1.0)

    yesterday_bids = []
    total_opponent_water_req = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
        total_opponent_water_req += opp['water_requirement']

    # Determine supply context
    can_i_get_my_water = day_context['supply'] >= WATER_REQ
    is_supply_abundant_for_all = day_context['supply'] >= (WATER_REQ + total_opponent_water_req)

    bid_amount = 0.0

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # High pressure scenario: Opponents bid very high yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3 and is_supply_abundant_for_all:
                # Can afford to lose HP and supply is abundant, try to conserve
                bid_amount = DAILY_SALARY * 0.3
            else:
                # Critical HP OR supply is scarce, must bid high
                bid_amount = DAILY_SALARY * 0.95
        else:
            # Moderate pressure scenario: Opponents' highest bid was not super high
            # Adjust bid based on supply abundance
            if is_supply_abundant_for_all:
                # Supply is abundant for everyone, can try to get it cheaper
                bid_amount = max(DAILY_SALARY * 0.4, highest_prev_bid + 1.0)
            elif can_i_get_my_water:
                # Supply is competitive but I can still get my water, bid slightly above highest previous bid
                bid_amount = max(DAILY_SALARY * 0.6, highest_prev_bid + 2.0)
            else: # I cannot get my water (supply < WATER_REQ)
                if my_status['hp'] <= 1:
                    # Extremely desperate, bid high just in case of edge allocation rules
                    bid_amount = DAILY_SALARY * 0.95
                else:
                    # Conserve budget, no point bidding high if I can't get water
                    bid_amount = 1.0

    else: # No yesterday's bids available (e.g., first day, or all opponents were inactive)
        if my_status['hp'] <= 2: # Critical HP
            bid_amount = DAILY_SALARY * 0.9
        elif my_status['no_water_days'] > 0: # Missed water yesterday
            bid_amount = DAILY_SALARY * 0.8
        elif is_supply_abundant_for_all:
            # Abundant supply, no history, bid conservatively
            bid_amount = DAILY_SALARY * 0.4
        elif can_i_get_my_water:
            # Competitive supply, no history, bid moderately
            bid_amount = DAILY_SALARY * 0.6
        else: # I cannot get my water
            if my_status['hp'] <= 1:
                bid_amount = DAILY_SALARY * 0.9
            else:
                bid_amount = 1.0

    # Ensure bid does not exceed budget and is at least 1.0
    final_bid = min(my_status['budget'], bid_amount)
    if num_alive_opponents > 0 and final_bid < 5.0 and can_i_get_my_water: 
        # Ensure a reasonable minimum bid if water is possible and competition exists
        final_bid = 5.0
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If I'm the only one left, bid minimally
    if num_alive_opponents == 0:
        return min(my_status['budget'], 1.0)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # Determine a base bid based on my HP and no_water_days
    if my_status['hp'] <= 2: # Critical HP, must get water
        bid_value = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP, prioritize getting water
        bid_value = DAILY_SALARY * 0.8
    elif my_status['no_water_days'] > 0: # Missed water yesterday, need to secure
        bid_value = DAILY_SALARY * 0.75
    else: # Healthy HP
        bid_value = DAILY_SALARY * 0.6 # Moderate base bid

    # Adjust bid based on opponent behavior (yesterday's highest bid)
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents are bidding very high
            # If my HP is not critical, try to match/slightly exceed, but don't overcommit too much
            if my_status['hp'] > 2:
                bid_value = max(bid_value, highest_prev_bid + 2)
            else: # If HP is critical, outbid aggressively
                bid_value = max(bid_value, highest_prev_bid + 5) # More aggressive
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Opponents are bidding moderately
            bid_value = max(bid_value, highest_prev_bid + 1) # Slightly higher to secure
        else: # Opponents are bidding low
            # Given supply is always tight for multiple agents, I still need to bid reasonably
            bid_value = max(bid_value, DAILY_SALARY * 0.55) # Ensure it's not too low but still competitive

    # Cap the bid to prevent overspending beyond daily salary (unless critical HP)
    if my_status['hp'] > 2:
        bid_value = min(bid_value, DAILY_SALARY * 1.05) # Cap at 105% of salary if not critical
    else: # If critical HP, allow bidding up to 120% of salary if budget allows
        bid_value = min(bid_value, DAILY_SALARY * 1.2)

    # Ensure bid is at least 1.0 if budget allows and I need water
    if bid_value < 1.0 and my_status['budget'] > 0:
        bid_value = 1.0

    # Final check: ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], bid_value)

    # If budget is 0, bid 0
    if my_status['budget'] == 0:
        final_bid = 0.0

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid low to save money
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid strategy based on my current HP
    bid = 0.0
    if my_status['hp'] <= 2: # Critical HP
        bid = DAILY_SALARY * 0.95
        if highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid + 1.0) # Ensure I get water if others bid high
    elif my_status['hp'] <= 5: # Low HP
        bid = DAILY_SALARY * 0.8
        if highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid + 1.0) # Compete strongly
    else: # Healthy HP
        if highest_prev_bid > 0:
            # If opponents are bidding very high, I must compete
            if highest_prev_bid >= DAILY_SALARY * 0.85: 
                bid = highest_prev_bid + 1.0
            # If opponents are bidding moderately, try to slightly outbid or maintain a good bid
            elif highest_prev_bid >= DAILY_SALARY * 0.5:
                bid = max(DAILY_SALARY * 0.55, highest_prev_bid + 1.0)
            # If opponents are bidding low, be conservative but still aim for water
            else:
                bid = DAILY_SALARY * 0.45
        else:
            # No previous bids from alive opponents, or all bid 0. Be moderately conservative.
            bid = DAILY_SALARY * 0.5 # Default for healthy HP and no clear high competition

    # Ensure bid does not exceed budget and is non-negative
    bid = min(bid, my_status['budget'])
    bid = max(0.0, bid)

    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None and prev_trace['bid'] > 0:
            yesterday_bids.append(prev_trace['bid'])

    base_bid = 0.0

    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.85
    else:
        if yesterday_bids:
            max_prev_bid = max(yesterday_bids)
            if max_prev_bid >= DAILY_SALARY * 0.8:
                base_bid = min(DAILY_SALARY * 0.9, max_prev_bid + 2.0)
            elif max_prev_bid >= DAILY_SALARY * 0.6:
                base_bid = max_prev_bid + 1.5
            else:
                base_bid = DAILY_SALARY * 0.65
        else:
            base_bid = DAILY_SALARY * 0.6

    final_bid = max(1.0, base_bid)
    final_bid = min(final_bid, my_status['budget'])
    
    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Default bid (moderate)
    bid_amount = DAILY_SALARY * 0.55 # Base bid of 82.5

    # If no active opponents, bid low to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3) # Bid 45 if no competition

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Adjust bid based on my health
    if my_status['hp'] <= 3 or my_status['no_water_days'] > 0:
        bid_amount = DAILY_SALARY * 0.95 # Critical health, bid very high (142.5)
    elif my_status['hp'] <= 5:
        bid_amount = DAILY_SALARY * 0.8 # Low health, bid high (120)

    # Adjust bid based on supply
    supply = day_context['supply']
    if supply < 20: # Supply is tighter
        bid_amount += DAILY_SALARY * 0.05 # Add 7.5
    else: # Supply is more abundant
        bid_amount -= DAILY_SALARY * 0.02 # Subtract 3

    # Adjust bid based on opponent's previous day bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.8: # If opponents were aggressive (bids >= 120)
            if my_status['hp'] > 5 and my_status['no_water_days'] == 0: # If healthy, try to be competitive but save
                bid_amount = max(bid_amount, highest_prev_bid * 0.95) # Bid slightly below, but ensure it's not too low
                bid_amount = min(bid_amount, DAILY_SALARY * 0.85) # Cap healthy bid at 127.5
            else: # Not healthy, must outbid
                bid_amount = max(bid_amount, highest_prev_bid + 3.0) # Ensure I win
        else: # Opponents were not extremely aggressive
            bid_amount = max(bid_amount, highest_prev_bid + 1.5) # Bid slightly above to secure water
    elif not yesterday_bids and my_status['hp'] > 5 and my_status['no_water_days'] == 0: # Day 1 or no trace, and healthy
        # If no previous bids and healthy, use a slightly more conservative default
        bid_amount = DAILY_SALARY * 0.6 # Moderate bid of 90

    # Final bid cannot exceed current budget and must be non-negative
    final_bid = min(my_status['budget'], bid_amount)
    final_bid = max(0.0, final_bid)
    final_bid = round(final_bid, 2)

    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    # Base bid: Start with a reasonable percentage of daily salary
    # This value aims to be competitive but not overly aggressive initially
    base_bid = DAILY_SALARY * 0.75 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4) # Bid 40% of salary if no competition

    # --- Adjust bid based on my HP ---
    if my_status['hp'] <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95 
    elif my_status['hp'] <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.85
    
    # --- Analyze opponent behavior from previous_trace ---
    highest_opponent_prev_bid = 0.0
    eric_prev_bid = 0.0
    eric_alive = False

    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                current_opp_bid = prev['bid']
                highest_opponent_prev_bid = max(highest_opponent_prev_bid, current_opp_bid)
                
                if opp_id == 'Eric':
                    eric_prev_bid = current_opp_bid
                    eric_alive = True
    
    # --- Adjust bid based on highest previous opponent bid ---
    if highest_opponent_prev_bid > 0:
        # If the highest bid was already very high, we need to exceed it slightly
        if highest_opponent_prev_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, highest_opponent_prev_bid + 2.0)
        elif highest_opponent_prev_bid >= DAILY_SALARY * 0.6:
            base_bid = max(base_bid, highest_opponent_prev_bid + 1.0)
        else: # If highest bid was moderate, ensure we are above it
            base_bid = max(base_bid, highest_opponent_prev_bid + 0.5)

    # --- Specific adjustment for Eric, given his historical high bidding ---
    if eric_alive and eric_prev_bid > 0:
        # If Eric is alive and previously bid high, we must be very competitive
        # Check Eric's current HP - if low, he might bid even more aggressively
        eric_status = opponents_status['Eric']
        if eric_status['hp'] <= 3: # Eric is desperate
            base_bid = max(base_bid, DAILY_SALARY * 0.9)
        elif eric_prev_bid > DAILY_SALARY * 0.7: # Eric consistently bids high
            base_bid = max(base_bid, eric_prev_bid + 1.5) # Outbid Eric by a bit more

    # --- Adjust bid based on supply pressure ---
    # Estimate total demand (my requirement + alive opponents' requirements)
    total_estimated_demand = WATER_REQ
    for opp in alive_opponents:
        total_estimated_demand += opp['water_requirement']
        
    supply = day_context['supply']
    
    # If supply is significantly less than total demand, competition is fierce
    if supply < total_estimated_demand * 0.8: # Supply is less than 80% of total estimated demand
        base_bid = max(base_bid, DAILY_SALARY * 0.8) # Increase bid significantly

    # --- Final bid calculation and constraints ---
    final_bid = min(my_status['budget'], base_bid)
    
    # If it's the last day and I'm still alive, bid very aggressively
    if day_context['day'] == 10 and my_status['hp'] > 0:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.99)
        
    # If budget is critically low but I need to survive, bid everything
    if my_status['hp'] <= 1 and my_status['budget'] > 0 and final_bid < my_status['budget'] * 0.5:
        final_bid = my_status['budget']

    # Ensure bid is not negative and at least a minimal amount if budget allows
    final_bid = max(0.0, final_bid)
    if final_bid == 0 and my_status['budget'] > 0:
        final_bid = 1.0 # Bid a minimal amount if budget allows to participate

    return final_bid
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

    # If no opponents, bid conservatively to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Initialize a base bid. This will be adjusted.
    current_bid = DAILY_SALARY * 0.5

    # --- Aggressiveness based on my status (HP, no_water_days, day) ---
    # Critical survival mode
    if my_status['hp'] <= 3 or my_status['no_water_days'] > 0:
        # High bid, with increasing urgency towards the end of the episode
        current_bid = max(current_bid, DAILY_SALARY * 0.95 + (EPISODE_DAYS - day_context['day']) * 2)
    # Late game urgency
    elif day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days
        current_bid = max(current_bid, DAILY_SALARY * 0.9)
    elif day_context['day'] >= EPISODE_DAYS - 4: # Last 4 days
        current_bid = max(current_bid, DAILY_SALARY * 0.75)
    
    # --- Adjust based on opponent's highest previous bid ---
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid > DAILY_SALARY: # Opponents are already bidding more than daily salary
            # If I'm very healthy, have good budget, and it's early/mid game, try to make them overspend
            if my_status['hp'] > 6 and my_status['budget'] > DAILY_SALARY * 3 and day_context['day'] < int(EPISODE_DAYS / 2): # CRITICAL INDEX RULE: int()
                current_bid = max(current_bid, highest_prev_bid * 0.95) # Bid slightly below to test their resolve
            else:
                # Otherwise, be highly competitive to secure water
                current_bid = max(current_bid, highest_prev_bid + 5.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents were very aggressive but within daily salary
            current_bid = max(current_bid, highest_prev_bid + 2.0)
        else: # Opponents were moderately or relatively conservative
            current_bid = max(current_bid, highest_prev_bid + 1.0)

    # Final bid must not exceed budget and must be at least 1.0
    final_bid = min(my_status['budget'], current_bid)
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    num_active_players = len(alive_opponents) + 1
    is_supply_tight = day_context['supply'] < (num_active_players * WATER_REQ * 1.2)
    
    bid = DAILY_SALARY * 0.55 # Default moderate bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.8: # High competition (e.g., Alex)
            if my_status['hp'] > 5: 
                if is_supply_tight:
                    bid = min(DAILY_SALARY * 0.9, highest_prev_bid + 5)
                else:
                    bid = DAILY_SALARY * 0.7
            else: # Low HP, need water desperately
                bid = min(DAILY_SALARY * 0.98, highest_prev_bid + 10)
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # Moderate competition (e.g., Eric)
            if is_supply_tight:
                bid = max(DAILY_SALARY * 0.7, highest_prev_bid + 2)
            else:
                bid = DAILY_SALARY * 0.6
        else: # Low previous bids
            if is_supply_tight:
                bid = max(DAILY_SALARY * 0.65, highest_prev_bid + 5)
            else:
                bid = DAILY_SALARY * 0.5
    
    # Critical HP overrides other logic
    if my_status['hp'] <= 3:
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5:
        bid = max(bid, DAILY_SALARY * 0.8)

    # If I missed water yesterday, ensure a strong bid for today
    if my_status['no_water_days'] > 0:
        if my_status['hp'] > 5:
            bid = max(bid, DAILY_SALARY * 0.7)
        else:
            bid = max(bid, DAILY_SALARY * 0.9)

    final_bid = min(my_status['budget'], bid)
    
    # Ensure a minimal bid if budget allows, to avoid bidding 0 when water is needed
    if final_bid <= 0 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.1)
    
    return final_bid
"""
