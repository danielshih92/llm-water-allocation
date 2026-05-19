# ============================================================
# Experiment: exp_077
# Agent: Cindy
# Source: exp_077
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to get water
    if not alive_opponents:
        return min(my_status['budget'], 1)

    # --- Analyze opponent previous bids ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # --- Base bid strategy ---
    # Start with a moderate bid, adjusted by my HP and supply
    
    # 1. Base on my HP
    my_bid = DAILY_SALARY * 0.55 # Default moderate bid
    if my_status['hp'] <= 2: # Critical HP
        my_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP
        my_bid = DAILY_SALARY * 0.75
    
    # 2. Adjust based on supply scarcity and competition
    # Estimate total water needed by all active players (myself included)
    estimated_total_demand = sum([o['water_requirement'] for o in alive_opponents]) + WATER_REQ
    
    # Avoid division by zero if demand is 0 (should not happen with WATER_REQ > 0)
    if estimated_total_demand > 0:
        supply_per_demand = day_context['supply'] / estimated_total_demand
        if supply_per_demand < 0.8: # Very scarce
            my_bid *= 1.2
        elif supply_per_demand < 1.0: # Scarce
            my_bid *= 1.1
        elif supply_per_demand > 1.5: # Abundant
            my_bid *= 0.8
    
    # 3. Adjust based on opponent's previous behavior (if available)
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were very aggressive yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # I'm relatively healthy, might try to conserve
                my_bid = min(my_bid, DAILY_SALARY * 0.3) # Conserve if possible
            else: # I need water, must compete aggressively
                my_bid = max(my_bid, highest_prev_bid + 5) # Bid slightly above to win
        # If opponents were moderately aggressive, or just generally competitive
        else:
            # Ensure my bid is at least slightly above what they were bidding if it makes sense
            my_bid = max(my_bid, highest_prev_bid + 1.5)

    # Ensure bid is at least 1 and does not exceed budget
    final_bid = max(1, min(my_status['budget'], my_bid))

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

    # Base bid, slightly above Eric's average from previous meta-round to be competitive
    bid = DAILY_SALARY * 0.65 # 97.5

    # Identify Eric, our main competitor
    eric = None
    for opp_id, opp_data in opponents_status.items():
        if opp_id == "Eric":
            eric = opp_data
            break

    # Adjust bid based on my HP and no_water_days (emergency mode)
    if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1:
        bid = DAILY_SALARY * 0.9 # Aggressive bid if in trouble
    elif my_status['hp'] > 7: # If doing well, try to save a bit
        bid = DAILY_SALARY * 0.55 # 82.5

    # Adjust bid based on supply availability
    supply = day_context['supply']
    if supply <= WATER_REQ + 5: # Supply is tight for two players needing water
        bid = max(bid, DAILY_SALARY * 0.75) # Ensure competitiveness
    elif supply >= WATER_REQ * 2: # Plenty of water, try to save
        bid = min(bid, DAILY_SALARY * 0.6) # Try to save

    # React to Eric's previous bid if he is alive and has a trace
    if eric and eric['alive'] and eric.get('previous_trace'):
        eric_prev_bid = eric['previous_trace'].get('bid')
        if eric_prev_bid is not None:
            # If Eric bid high and won, assume he's competitive, bid slightly higher
            if eric_prev_bid >= DAILY_SALARY * 0.7:
                bid = max(bid, eric_prev_bid + 5)
            # If Eric bid very low and I'm healthy, try to save more
            elif eric_prev_bid < DAILY_SALARY * 0.4 and my_status['hp'] > 5:
                bid = min(bid, DAILY_SALARY * 0.5)
    
    # Final adjustment for end game (last 2 days)
    if day_context['day'] >= EPISODE_DAYS - 2:
        bid = max(bid, DAILY_SALARY * 0.8) # Be very aggressive to finish
        if my_status['hp'] <= 2:
             bid = DAILY_SALARY * 0.95 # Max aggressive if in dire straits at end

    # Ensure bid does not exceed current budget
    bid = min(bid, my_status['budget'])

    # Ensure bid is not negative
    bid = max(0.0, bid)

    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    # Initialize a base bid
    # This bid aims to be competitive but not overly aggressive when HP is good
    base_bid = DAILY_SALARY * 0.65

    # Adjust bid based on my current HP
    if my_status['hp'] <= 2: # Critical HP, must win
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP, need water
        base_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] >= 8: # Healthy HP, can afford to be more conservative
        base_bid = DAILY_SALARY * 0.55

    # Analyze yesterday's bids from alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # Adjust bid based on opponent's previous behavior
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If highest bid was very high (aggressive opponent)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 5: # If healthy, consider backing off to save budget
                # Try to win cheaply if others overbid, or conserve if I don't need water urgently
                current_bid = min(base_bid, highest_prev_bid * 0.8) # Bid less than high bid
                current_bid = max(current_bid, DAILY_SALARY * 0.4) # Ensure it's not too low
            else: # HP is low or critical, must compete
                current_bid = max(base_bid, highest_prev_bid + 5) # Bid to win
        elif highest_prev_bid >= DAILY_SALARY * 0.65: # Moderate competition
            current_bid = max(base_bid, highest_prev_bid + 2) # Bid slightly above to secure
        else: # Low competition yesterday
            current_bid = max(base_bid, average_prev_bid * 1.1) # Bid slightly above average
            current_bid = min(current_bid, DAILY_SALARY * 0.7) # Cap to avoid overbidding unnecessarily
    else:
        # No previous bids or no alive opponents, use the calculated base bid
        current_bid = base_bid

    # Further adjustment for end game
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] <= 6: # Last 2 days and not super healthy
        current_bid = max(current_bid, DAILY_SALARY * 0.9) # Be very aggressive to survive

    # Ensure bid is not negative and does not exceed current budget
    final_bid = max(0.0, current_bid)
    return min(my_status['budget'], final_bid)
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
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid - a reasonable amount to secure water
    base_bid = DAILY_SALARY * 0.5

    # 1. Adapt bid based on my HP
    if my_hp <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.8
    elif my_hp >= 8: # High HP, can be more conservative
        base_bid = DAILY_SALARY * 0.4

    # 2. Adapt bid based on day progression
    # Increase bid as the game progresses and survival becomes more critical
    # Day factor scales from 1 (Day 0) to 1.5 (Day EPISODE_DAYS)
    day_factor = 1 + (current_day / EPISODE_DAYS) * 0.5
    base_bid *= day_factor

    # 3. Adapt bid based on supply scarcity
    # If supply is low, competition is higher
    shortage_ratio = 0
    if num_alive_opponents > 0:
        # Calculate how many agents cannot get water (positive if demand > supply)
        shortage_ratio = max(0, (num_alive_opponents - current_supply) / num_alive_opponents)
        base_bid *= (1 + shortage_ratio * 0.5) # Increase bid if there's a shortage

    # 4. Adapt bid based on opponent's previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        if my_hp <= 4: # Desperate: try to beat the highest bid
            base_bid = max(base_bid, highest_prev_bid + 5)
        elif my_hp > 4 and highest_prev_bid >= DAILY_SALARY * 0.8: # Opponent bid aggressively, but I'm not desperate
            base_bid = max(base_bid, average_prev_bid * 1.1) # Bid above average to stay competitive
        else: # Opponents not overly aggressive, or I have good HP
            base_bid = max(base_bid, average_prev_bid * 1.05) # Slightly above average to win

    # Ensure bid is not negative and does not exceed my budget
    final_bid = min(my_budget, max(0.1, base_bid)) # Minimum bid of 0.1 to always participate
    
    # Cap bid at a reasonable maximum, e.g., 1.5 times daily salary, unless very desperate
    if my_hp > 2:
        final_bid = min(final_bid, DAILY_SALARY * 1.5) 
    
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
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        return max(1, min(my_budget, DAILY_SALARY * 0.1))

    # Calculate base bid based on my HP
    if my_hp <= 2: # Critical HP, must win
        base_bid = DAILY_SALARY * 0.9
    elif my_hp <= 5: # Low HP
        base_bid = DAILY_SALARY * 0.7
    else: # Healthy HP
        base_bid = DAILY_SALARY * 0.5

    # Adjust based on remaining days (end game pressure)
    days_remaining = EPISODE_DAYS - current_day
    if days_remaining <= 2: # Last 2 days, bid very aggressively
        base_bid = max(base_bid, DAILY_SALARY * 0.95)
    elif days_remaining <= 4: # Mid-late game
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    # Analyze opponent's previous bids from 'previous_trace'
    highest_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])

    # React to highest previous bid
    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents bid very high
            if my_hp <= 3: # My HP is low, I need to outbid
                base_bid = max(base_bid, highest_prev_bid + 10)
            else: # My HP is okay, try to slightly outbid or match
                base_bid = max(base_bid, highest_prev_bid + 2)
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Opponents bid moderately
            base_bid = max(base_bid, highest_prev_bid + 1)

    # Adjust for supply scarcity
    # If supply is less than what two agents need, it's very competitive
    if current_supply < WATER_REQ * 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.75) # Increase bid due to scarcity
    elif current_supply < WATER_REQ * (num_alive_opponents + 1): # Supply might not be enough for all
        base_bid = max(base_bid, DAILY_SALARY * 0.6)

    # Final bid cannot exceed budget and must be at least 1
    final_bid = max(1, min(my_budget, base_bid))

    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    # Focus on known competitive opponents: Alex and Bob
    alive_opponents = [o for o_id, o in opponents_status.items() if o['alive'] and o_id in ["Alex", "Bob"]]

    # Default highest previous bid if no relevant opponents or no trace data
    highest_prev_bid = 0.0
    yesterday_bids = []

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Determine base bid strategy
    # A good starting point, slightly below salary, to be competitive but not overspend initially
    base_bid = DAILY_SALARY * 0.8 

    # Adjust base bid based on opponent's highest previous bid
    if highest_prev_bid > DAILY_SALARY: # Opponents are bidding above salary, indicating high competition/desperation
        base_bid = highest_prev_bid + 5 # Try to outbid them slightly
    elif highest_prev_bid > DAILY_SALARY * 0.7: # Opponents are bidding competitively but within salary range
        base_bid = highest_prev_bid + 2 # Slightly outbid to secure water
    else: # Opponents were conservative or didn't bid much (e.g., first day or weak opponents)
        base_bid = max(DAILY_SALARY * 0.6, highest_prev_bid + 1) # Ensure we don't bid too low, but stay competitive

    # Adjust bid based on my HP and no_water_days
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0: # Critical HP or missed water: Bid very aggressively
        bid = DAILY_SALARY * 1.2 # Bid significantly above salary if budget allows
        bid = max(bid, highest_prev_bid + 10) # Ensure we outbid if desperate to survive
    elif my_status['hp'] <= 5: # Low HP: Bid aggressively
        bid = DAILY_SALARY * 1.05 # Slightly above salary to secure water
        bid = max(bid, highest_prev_bid + 5)
    else: # Healthy HP: Bid competitively based on the calculated base_bid
        bid = base_bid

    # Ensure the bid is at least a certain minimum to be considered competitive
    min_competitive_bid = DAILY_SALARY * 0.7
    bid = max(bid, min_competitive_bid)

    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], bid)
    
    # Ensure the bid is at least 1.0, unless budget is 0
    return max(1.0, final_bid) if my_status['budget'] > 0 else 0.0
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    # If current supply is less than my requirement, I cannot get water. Bid 0 to save budget.
    if current_supply < WATER_REQ:
        return 0.0

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If I'm the only one left, bid minimally to ensure win and save budget.
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1) # Bid 10% of salary

    # Calculate how many full water requirements can be met from current supply
    num_full_reqs_possible = int(current_supply // WATER_REQ)

    # Base bid - start with a moderate value
    base_bid = DAILY_SALARY * 0.5

    # --- Adjust bid based on survival needs (HP) ---
    if my_hp <= 2: # Critical HP, must get water
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.8
    elif my_hp >= 8: # High HP, can afford to be more conservative
        base_bid = DAILY_SALARY * 0.4

    # --- Adjust bid based on supply scarcity and competition ---
    # If supply is very tight (fewer slots than active players + me)
    if num_full_reqs_possible <= num_alive_opponents:
        base_bid *= 1.2 # Increase bid due to high competition
    # If supply is abundant (many more slots than active players + me)
    elif num_full_reqs_possible > num_alive_opponents + 1:
        base_bid *= 0.8 # Decrease bid to save money

    # --- Adjust bid based on day in episode ---
    if current_day > EPISODE_DAYS * 0.7: # Later days, higher stakes
        base_bid *= 1.1
    elif current_day < EPISODE_DAYS * 0.3: # Early days, less pressure
        base_bid *= 0.9

    # --- React to opponent's previous bids (yesterday's trace) ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents were bidding aggressively yesterday, I need to be competitive
        if max_yesterday_bid > DAILY_SALARY * 0.7: # High bids from opponents
            # Bid slightly above max or a good margin above average
            base_bid = max(base_bid, max_yesterday_bid + (DAILY_SALARY * 0.05)) # Bid 5% of salary above max
        elif avg_yesterday_bid > DAILY_SALARY * 0.5: # Moderate bids from opponents
            base_bid = max(base_bid, avg_yesterday_bid + (DAILY_SALARY * 0.02)) # Bid 2% of salary above average

        # If my HP is good and opponents bid low, try to win cheaply
        if my_hp > 5 and max_yesterday_bid < DAILY_SALARY * 0.4:
            base_bid = min(base_bid, max_yesterday_bid + 1.0) # Bid just above their max

    # Final bid must be non-negative and not exceed current budget
    final_bid = max(0.0, min(my_budget, base_bid))

    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13

    current_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        # If no opponents are alive, bid a minimal amount to secure water
        # Ensure it's at least 1.0 to win against 0 bids and not exceed budget.
        return min(current_budget, DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        # Only consider valid bids that did not result in an error
        if prev and prev.get('bid') is not None and prev.get('status') != 'error':
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.5 # Default moderate bid if no strong history

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Bid slightly above the highest opponent bid from yesterday to outcompete
        base_bid = max(base_bid, highest_prev_bid + 5.0)
    else:
        # If it's day 1 or no successful bids yesterday, use a sensible default
        # Be more aggressive if there are many opponents to secure water early
        if len(alive_opponents) > 1:
            base_bid = DAILY_SALARY * 0.8
        else:
            base_bid = DAILY_SALARY * 0.6

    final_bid = base_bid

    # Adjust bid based on my HP for survival
    if my_status['hp'] <= 2: # Critical HP: bid very aggressively, nearly all budget
        final_bid = max(final_bid, DAILY_SALARY * 1.2)
        final_bid = max(final_bid, current_budget * 0.95) # Use most of budget if critical
    elif my_status['hp'] <= 4: # Low HP: be aggressive
        final_bid = max(final_bid, DAILY_SALARY * 1.0)
    else: # Healthy HP: try to save budget, but still aim to win
        final_bid = max(final_bid, DAILY_SALARY * 0.7)

    # Ensure bid does not exceed current budget
    final_bid = min(current_budget, final_bid)

    # Ensure bid is at least 1.0 and positive
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    current_budget = my_status['budget']
    current_hp = my_status['hp']
    current_supply = day_context['supply']
    current_day = day_context['day']
    
    # Calculate a supply scarcity factor (1.0 for min supply, 0.0 for max supply)
    supply_scarcity_factor = 1.0 - ((current_supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))
    
    # Base bid ranges from 50% to 90% of daily salary, adjusted by supply scarcity
    # Higher scarcity (lower supply) leads to a higher base bid.
    base_bid_amount = DAILY_SALARY * (0.5 + 0.4 * supply_scarcity_factor) # Ranges from 75.0 to 135.0

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        # No opponents, bid minimum to get water and save budget.
        return min(current_budget, DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    target_bid = base_bid_amount

    if yesterday_bids:
        max_opp_bid = max(yesterday_bids)
        avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids)
        
        # If opponents bid very high, try to outbid them.
        if max_opp_bid > DAILY_SALARY * 0.7:
            target_bid = max(target_bid, max_opp_bid + 5.0)
        else:
            # Otherwise, bid slightly above average to secure water.
            target_bid = max(target_bid, avg_opp_bid * 1.1)

    # Adjust bid based on my HP (survival priority)
    if current_hp <= 3: # Critical HP
        target_bid = max(target_bid, DAILY_SALARY * 0.95)
    elif current_hp <= 6: # Low HP
        target_bid = max(target_bid, DAILY_SALARY * 0.8)
    
    # Adjust bid for end-game push if still alive
    remaining_days = 10 - current_day
    if remaining_days <= 3 and current_hp > 0: 
        target_bid = max(target_bid, DAILY_SALARY * 0.9)
    
    # Ensure bid does not exceed current budget
    final_bid = min(current_budget, target_bid)
    
    # Ensure bid is at least a small positive amount to participate
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state, assuming it's constant

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents are alive, bid a minimal amount to secure water
    if num_alive_opponents == 0:
        return min(my_status['budget'], 1.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid: Start with a competitive bid, slightly above average strong opponent bids
    base_bid = DAILY_SALARY * 0.6 # e.g., 90 for DAILY_SALARY 150

    # Adjust based on yesterday's highest bid from alive opponents
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Aggressive previous bid (e.g., >= 120)
            base_bid = max(base_bid, highest_prev_bid * 1.05) # Try to outbid by 5%
        elif highest_prev_bid < DAILY_SALARY * 0.4: # Low previous bids (e.g., < 60)
            base_bid = min(base_bid, highest_prev_bid * 1.2) # Still try to outbid, but not too much
        else: # Moderate previous bids (e.g., 60-120)
            base_bid = max(base_bid, highest_prev_bid + 5) # Slightly higher than previous

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP, must get water
        base_bid = max(base_bid, DAILY_SALARY * 0.95) # Bid almost full salary
    elif my_status['hp'] <= 4: # Low HP, prioritize water
        base_bid = max(base_bid, DAILY_SALARY * 0.8) # Bid high

    # Adjust bid based on current supply
    current_supply = day_context['supply']
    total_water_required = WATER_REQ # My requirement
    for opp in alive_opponents:
        total_water_required += opp['water_requirement'] # Add opponents' requirements

    if current_supply < total_water_required * 0.7: # Very scarce supply
        base_bid *= 1.2
    elif current_supply < total_water_required * 0.9: # Scarce supply
        base_bid *= 1.1
    elif current_supply > total_water_required * 1.5: # Abundant supply
        base_bid *= 0.8
    elif current_supply > total_water_required * 1.2: # Decent surplus
        base_bid *= 0.9

    # Further adjustment for very low supply relative to my own requirement
    if current_supply <= WATER_REQ + num_alive_opponents: # Supply is barely enough for everyone to get 1 unit + my water
         base_bid *= 1.15 # Be more aggressive

    # Day progression adjustment
    current_day = day_context['day']
    remaining_days = EPISODE_DAYS - current_day

    # Late game aggression if budget allows
    if remaining_days <= 3 and my_status['budget'] >= DAILY_SALARY * (remaining_days + 1):
        base_bid *= 1.1
    # Early game conservation if HP is good
    elif current_day <= 3 and my_status['hp'] >= 5:
        base_bid *= 0.9

    # Final bid must be non-negative and not exceed current budget
    final_bid = min(my_status['budget'], max(0.0, base_bid))

    # Ensure a minimal bid if there are opponents and budget allows, to avoid bidding 0
    if num_alive_opponents > 0 and final_bid < 1.0 and my_status['budget'] >= 1.0:
        final_bid = 1.0

    return final_bid
"""
