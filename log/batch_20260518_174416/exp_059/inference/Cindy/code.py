# ============================================================
# Experiment: exp_059
# Agent: Cindy
# Source: exp_059
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid a minimal amount to get water and save budget
    if not alive_opponents:
        return min(my_status['budget'], WATER_REQ * 2) # Bid 26 as a safe, low amount

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine bid based on my status and opponent's previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if my_status['hp'] <= 2: # Very desperate
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        elif my_status['hp'] <= 4: # Getting desperate
            # Bid aggressively above previous high, but capped by a high salary percentage
            return min(my_status['budget'], max(highest_prev_bid + 5, DAILY_SALARY * 0.75))
        else: # Healthy HP (my_status['hp'] > 4)
            if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents were very aggressive yesterday
                # Stay competitive, bid slightly above, but try to save a bit if possible
                return min(my_status['budget'], max(highest_prev_bid + 1, DAILY_SALARY * 0.6))
            else: # Opponents were moderate or low yesterday
                # Bid slightly above to secure water, or a moderate amount
                return min(my_status['budget'], max(highest_prev_bid + 1, DAILY_SALARY * 0.5))
    else: # No yesterday bids (e.g., first day of meta-round or no trace available)
        if my_status['hp'] <= 2: # Very desperate
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        elif my_status['hp'] <= 4: # Getting desperate
            return min(my_status['budget'], DAILY_SALARY * 0.7)
        else: # Healthy HP (my_status['hp'] > 4)
            # Start with a moderate bid to test the waters
            return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10
    
    # My intrinsic value for one unit of water, based on my daily salary
    # This is the maximum I can afford *per unit* if I want to sustain myself daily
    MY_SUSTAINABLE_VALUE_PER_UNIT = DAILY_SALARY / WATER_REQ 

    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to secure water and save budget
    if not alive_opponents:
        # Bid a low amount per unit, ensuring it's affordable for WATER_REQ units
        # and that it's not zero to actually win something.
        return max(0.1, min(my_status['budget'] / WATER_REQ, MY_SUSTAINABLE_VALUE_PER_UNIT * 0.1))

    yesterday_bids = []
    total_water_demand = WATER_REQ # My demand
    
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
        total_water_demand += opp['water_requirement']

    # Determine a base bid
    base_bid_per_unit = MY_SUSTAINABLE_VALUE_PER_UNIT * 0.7 # Start a bit below my sustainable value

    # Adjust based on supply-demand pressure
    # If demand significantly exceeds supply, increase base bid
    if total_water_demand > current_supply:
        # Scale up the bid based on how much demand exceeds supply
        # But don't exceed a certain multiplier of my sustainable value
        pressure_multiplier = 1 + (total_water_demand - current_supply) / total_water_demand * 0.7
        base_bid_per_unit *= min(pressure_multiplier, 1.5) # Cap at 1.5x for demand pressure

    # Initialize bid_per_unit with the calculated base bid
    bid_per_unit = base_bid_per_unit

    # React to opponent's previous bids
    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents are bidding very high (e.g., much higher than my sustainable value)
        # This indicates I'm at a severe disadvantage given my high WATER_REQ.
        # The threshold of 2.5x MY_SUSTAINABLE_VALUE_PER_UNIT (approx 28.8) is chosen
        # because historical meta-round data shows bids often exceed this significantly.
        if highest_prev_bid > MY_SUSTAINABLE_VALUE_PER_UNIT * 2.5: 
            if my_status['hp'] > 3 and current_day < EPISODE_DAYS - 2: # If not desperate and early/mid game
                # Conserve budget, accept HP loss for now by bidding very low
                bid_per_unit = max(0.1, MY_SUSTAINABLE_VALUE_PER_UNIT * 0.1)
            else: # Desperate or late game, must compete as much as possible
                # Try to get close to the highest bid, but cap it to avoid immediate bankruptcy
                bid_per_unit = max(bid_per_unit, highest_prev_bid * 0.85)
                bid_per_unit = min(bid_per_unit, MY_SUSTAINABLE_VALUE_PER_UNIT * 3.5) # Max aggressive cap
        else: # Opponent bids are somewhat competitive but not impossible
            # Bid slightly above the highest previous bid to try and win
            bid_per_unit = max(base_bid_per_unit, highest_prev_bid + 0.5)
    
    # Desperation bid if HP is low
    # If my HP is critically low, I must bid very aggressively
    if my_status['hp'] <= 2:
        bid_per_unit = MY_SUSTAINABLE_VALUE_PER_UNIT * 2.0 # Bid 2x my sustainable value
        if current_day >= EPISODE_DAYS - 1: # Last day, even more desperate
             bid_per_unit = MY_SUSTAINABLE_VALUE_PER_UNIT * 3.0 # Even more aggressive

    # Ensure bid doesn't exceed available budget for my WATER_REQ
    # Calculate maximum per-unit bid I can afford right now
    max_affordable_per_unit_bid = my_status['budget'] / WATER_REQ
    
    # The final bid is the minimum of our calculated bid and what we can actually afford
    final_bid = min(bid_per_unit, max_affordable_per_unit_bid)

    # Ensure bid is not negative or zero if budget is extremely low, always bid at least 0.1
    return max(0.1, final_bid)
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

    # --- Opponent Analysis ---
    active_opponents_bids_yesterday = []
    num_active_opponents = 0
    total_active_water_demand = WATER_REQ # My demand
    
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            num_active_opponents += 1
            total_active_water_demand += opp_data['water_requirement']
            if 'previous_trace' in opp_data and opp_data['previous_trace'] and 'bid' in opp_data['previous_trace']:
                active_opponents_bids_yesterday.append(opp_data['previous_trace']['bid'])

    # --- Base Bid Calculation ---
    # Start with a moderate bid, slightly above what Alex/Bob historically bid
    base_bid = DAILY_SALARY * 0.5 # Default 75

    if active_opponents_bids_yesterday:
        max_opp_bid_yesterday = max(active_opponents_bids_yesterday)
        avg_opp_bid_yesterday = sum(active_opponents_bids_yesterday) / len(active_opponents_bids_yesterday)
        
        # If opponents were aggressive yesterday, match or slightly exceed their max
        if max_opp_bid_yesterday > DAILY_SALARY * 0.4: # e.g., > 60
            base_bid = max(base_bid, max_opp_bid_yesterday + 2.5) # Bid slightly above their max
        
        # Ensure we are competitive with their average
        base_bid = max(base_bid, avg_opp_bid_yesterday * 1.1) # 10% above avg

    # --- Health-based Adjustment ---
    bid_multiplier = 1.0
    if my_status['hp'] <= 3: # Critical HP
        bid_multiplier = 1.5 # Bid very aggressively
    elif my_status['no_water_days'] > 0: # Missed water yesterday
        bid_multiplier = 1.2 # Bid aggressively
    
    bid = base_bid * bid_multiplier

    # --- Supply and Competition Adjustment ---
    # If total demand significantly exceeds supply, increase bid
    if current_supply < total_active_water_demand:
        water_shortage_ratio = total_active_water_demand / current_supply
        # The more severe the shortage, the higher the bid multiplier
        # Scale bid based on this ratio, capping at 0.9 of daily salary for shortage factor
        bid_from_shortage = DAILY_SALARY * min(1.0, 0.5 + (water_shortage_ratio - 1.0) * 0.25)
        bid = max(bid, bid_from_shortage) # Ensure bid is at least this level

    # --- End-game Adjustment ---
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last 2 days
        bid = max(bid, DAILY_SALARY * 0.9) # Bid very high (135)
    elif remaining_days <= 4: # Last 4 days
        bid = max(bid, DAILY_SALARY * 0.75) # Bid high (112.5)

    # --- Final Bid Constraints ---
    final_bid = min(bid, my_status['budget'])

    # Ensure bid is not negative or zero if budget allows
    if final_bid <= 0 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], 1.0) # Bid a minimum if budget exists
    elif final_bid < 1.0 and my_status['budget'] >= 1.0: # Ensure a minimum bid if budget allows for it
        final_bid = 1.0

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

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_bidders = len(alive_opponents) + 1 # Me + alive opponents

    # --- 1. Base bid based on my health --- 
    if my_current_hp <= 2: # Critical health, bid very aggressively
        bid = DAILY_SALARY * 0.95
    elif my_no_water_days > 0: # Missed water yesterday, need to secure it
        bid = DAILY_SALARY * 0.85
    elif my_current_hp <= 5: # Low-ish health
        bid = DAILY_SALARY * 0.7
    else: # Healthy, moderate bid
        bid = DAILY_SALARY * 0.55

    # --- 2. Adjust bid based on opponent's previous bids --- 
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace')
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.85: # Opponents were very aggressive
            if my_current_hp > 4: # Healthy, try to conserve if possible
                bid = min(bid, DAILY_SALARY * 0.35) # Lower bid
            else: # Low HP, must match aggression
                bid = max(bid, highest_prev_bid + 5) # Bid slightly higher
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Opponents were moderately aggressive
            bid = max(bid, highest_prev_bid + 2.5) # Bid slightly higher to win
        else: # Opponents were conservative
            bid = max(bid, highest_prev_bid + 1) # Just barely beat them

    # --- 3. Adjust bid based on supply vs. demand pressure --- 
    # How many "slots" for water_req exist in the current supply
    num_water_slots = int(current_supply // WATER_REQ)

    if num_water_slots < num_bidders: # Scarcity: Not enough water for everyone to get their requirement
        # Increase bid, more aggressively if fewer slots available
        scarcity_multiplier = 1 + (num_bidders - num_water_slots) * 0.1
        bid *= scarcity_multiplier
        bid = min(bid, DAILY_SALARY * 0.99) # Cap aggressive bids
    else: # Abundance: Enough water for everyone, potentially more
        # Decrease bid, more conservatively
        abundance_multiplier = 1 - (num_water_slots - num_bidders) * 0.05
        bid *= abundance_multiplier
        bid = max(bid, DAILY_SALARY * 0.2) # Don't bid too low, ensure I get water

    # --- 4. Late game push/survival ---
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        if my_current_hp > 5 and my_current_budget > DAILY_SALARY * 1.5: # Healthy and rich, try to win
            bid = max(bid, DAILY_SALARY * 0.9)
        elif my_current_hp <= 3: # Low HP, desperate to survive
            bid = max(bid, DAILY_SALARY * 0.99)

    # --- 5. Final bid constraints --- 
    final_bid = max(0.0, bid) # Bid cannot be negative
    final_bid = min(my_current_budget, final_bid) # Cannot bid more than available budget
    final_bid = max(final_bid, 1.0) # Ensure a minimum bid to participate, avoid 0.0

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 1.0) # Bid minimally if no opponents

    yesterday_bids = []
    strong_opponents_yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            # Focus on known strong players from meta-round context
            if opp_id in ["Alex", "Eric"]:
                strong_opponents_yesterday_bids.append(prev['bid'])

    current_supply = day_context['supply']
    current_day = day_context['day']

    # Determine the highest bid from strong opponents, or overall if none from strong
    highest_relevant_prev_bid = 0.0
    if strong_opponents_yesterday_bids:
        highest_relevant_prev_bid = max(strong_opponents_yesterday_bids)
    elif yesterday_bids:
        highest_relevant_prev_bid = max(yesterday_bids)

    # Base bid strategy
    bid_amount = DAILY_SALARY * 0.55 # Default moderate bid

    # 1. Critical HP override: Bid very high to survive if HP is critically low
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.98)

    # 2. React to high competition from previous bids
    if highest_relevant_prev_bid >= DAILY_SALARY * 0.85: # If strong/general competition is very high
        # If supply is very scarce, be more aggressive
        if current_supply < WATER_REQ * 1.5: 
            bid_amount = max(bid_amount, DAILY_SALARY * 0.9)
        else:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.85) # High bid
    elif highest_relevant_prev_bid >= DAILY_SALARY * 0.6: # If competition is moderately high
        # If supply is very scarce, still be aggressive
        if current_supply < WATER_REQ * 1.5:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.8)
        else:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.7) # Moderate-high bid
    elif highest_relevant_prev_bid > 0: # Some previous bid exists, but not very high
        bid_amount = max(bid_amount, highest_relevant_prev_bid + 1.5) # Bid slightly above

    # 3. Adjust based on supply scarcity (if not already covered by previous bid reaction)
    if current_supply < WATER_REQ * 1.5: # Very scarce supply
        bid_amount = max(bid_amount, DAILY_SALARY * 0.8)
    elif current_supply < WATER_REQ * 2.0: # Moderately scarce supply
        bid_amount = max(bid_amount, DAILY_SALARY * 0.65)

    # 4. Adjust for end-game if HP is good
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_status['hp'] > remaining_days: # Near end and enough HP to skip water
        bid_amount = min(bid_amount, DAILY_SALARY * 0.3) # Conserve budget

    # Ensure bid does not exceed budget and is positive
    final_bid = min(my_status['budget'], bid_amount)
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

    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Base bid - a moderate amount to ensure competitiveness
    bid = DAILY_SALARY * 0.55

    # Adjust bid based on my HP (desperation)
    if my_status['hp'] <= 2: # Critical HP
        bid = DAILY_SALARY * 0.98 # Max bid to survive
    elif my_status['hp'] <= 4: # Low HP
        bid = DAILY_SALARY * 0.85
    # If HP is good, 'bid' remains at 0.55 * DAILY_SALARY or adjusted by other factors

    # Analyze yesterday's bids from opponents to react to competition
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

        # If opponents bid very high, consider strategy:
        # If my HP is good, let them deplete budget.
        # If my HP is low, I must win.
        if max_yesterday_bid >= DAILY_SALARY * 0.8: # Opponents bid very high
            if my_status['hp'] > 5: # My HP is good, can afford to back off and save budget
                bid = min(bid, DAILY_SALARY * 0.3) # Conserve
            else: # My HP is low or moderate, must compete
                bid = max(bid, max_yesterday_bid + 5) # Try to outbid
        elif max_yesterday_bid >= DAILY_SALARY * 0.5: # Moderate competition
            bid = max(bid, max_yesterday_bid + 2)
        else: # Low competition
            bid = max(bid, max_yesterday_bid + 1)
    # else: no yesterday bids, 'bid' is determined by HP or base bid.

    # Adjust bid based on supply scarcity
    if current_supply <= 15: # Very tight supply, only enough for ~1 player
        bid = max(bid, DAILY_SALARY * 0.8) # Bid very aggressively
    elif current_supply <= 20: # Medium tight supply, enough for ~1-2 players
        bid = max(bid, DAILY_SALARY * 0.65) # Bid moderately aggressively
    # If supply is > 20, the base bid or HP-adjusted bid is likely sufficient.

    # Adjust for end game pressure
    if current_day >= EPISODE_DAYS - 2: # Last 2-3 days
        if my_status['hp'] <= 5: # Critical or near critical
            bid = max(bid, DAILY_SALARY * 0.98) # Bid very high to survive
        elif my_status['budget'] >= DAILY_SALARY * (EPISODE_DAYS - current_day + 1): # Good budget remaining
            # Can afford to be more aggressive to secure wins
            bid = max(bid, DAILY_SALARY * 0.75) # Push hard

    # Ensure bid does not exceed my daily salary for sustainable play
    bid = min(bid, DAILY_SALARY * 1.0)

    # Final check: Don't bid more than actual budget
    final_bid = min(bid, my_status['budget'])

    # Ensure bid is at least a minimum to be competitive
    final_bid = max(final_bid, DAILY_SALARY * 0.1)

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid low to save budget.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # If there are previous bids to react to
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # High competition detected (highest previous bid was aggressive)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If healthy, let others overspend, bid conservatively.
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            # If HP is critical, bid very aggressively to survive.
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        # Moderate competition, try to win by slightly outbidding.
        return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))

    # No previous bids (e.g., first day or all opponents didn't bid).
    # Bid based on personal HP.
    if my_status['hp'] <= 2:
        # Critical HP, bid high to ensure water.
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    # Healthy, bid moderately.
    return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQUIREMENT = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    bid = 0.0

    if num_alive_opponents == 0:
        bid = min(my_budget, DAILY_SALARY * 0.1) # Minimal bid to get water
        return max(0.0, bid)

    remaining_days = EPISODE_DAYS - current_day + 1

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    if my_hp <= 2: # Critical HP: Must win at almost any cost
        bid = min(my_budget, DAILY_SALARY * 0.99)
    elif my_hp <= 4 or remaining_days <= 3: # Low HP or Late Game: Need to win
        if highest_prev_bid > 0:
            bid = min(my_budget, max(DAILY_SALARY * 0.9, highest_prev_bid + 15))
        else:
            bid = min(my_budget, DAILY_SALARY * 0.9)
    else: # Good HP: Can afford to be strategic
        if highest_prev_bid > 0:
            if highest_prev_bid >= DAILY_SALARY * 0.85: # Opponents are bidding very high
                if my_hp >= 8 and remaining_days > 5: # Very good HP and early/mid game, can risk losing a day
                    bid = min(my_budget, DAILY_SALARY * 0.6) # Conserve budget
                else: # Good HP but not excellent, or mid/late game, stay competitive
                    bid = min(my_budget, max(DAILY_SALARY * 0.8, highest_prev_bid + 8))
            else: # Opponents' bids are not extremely high yet, push them up
                bid = min(my_budget, max(DAILY_SALARY * 0.75, highest_prev_bid + 10))
        else:
            bid = min(my_budget, DAILY_SALARY * 0.8)

    return max(0.0, min(bid, my_budget))
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
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid a small amount to secure water and save budget.
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Determine base bid based on my HP
    # Higher HP means I can afford to be slightly less aggressive, lower HP means I need water more urgently.
    if my_status['hp'] <= 3:
        base_bid = DAILY_SALARY * 0.95 # Critical HP, bid almost full salary
    elif my_status['hp'] <= 6:
        base_bid = DAILY_SALARY * 0.8  # Low HP, bid strongly
    else:
        base_bid = DAILY_SALARY * 0.7  # Healthy HP, still competitive but some buffer

    # Collect yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

    # Find the highest bid among opponents yesterday
    max_opp_prev_bid = 0
    if yesterday_bids:
        max_opp_prev_bid = max(yesterday_bids)

    # Adjust bid to be competitive against the highest previous bid
    # If the highest opponent bid was higher than my calculated base bid, I need to raise my bid.
    # Since only one agent can satisfy their full requirement, I need to try to be the highest bidder.
    current_bid = base_bid
    if max_opp_prev_bid >= current_bid:
        # Bid slightly higher than the highest opponent bid, plus a small buffer
        current_bid = max_opp_prev_bid + (DAILY_SALARY * 0.05)
    
    # Consider Eric specifically, as he was a survivor and high bidder
    # This part ensures we specifically target Eric if he's a threat and his bid was higher
    eric_alive = False
    eric_prev_bid = 0
    for opp_id, opp in opponents_status.items():
        if opp_id == "Eric" and opp['alive']:
            eric_alive = True
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                eric_prev_bid = prev['bid']
            break

    if eric_alive and eric_prev_bid > current_bid:
        # If Eric's previous bid was even higher than my current competitive bid, adjust again
        current_bid = eric_prev_bid + (DAILY_SALARY * 0.05)

    # If it's the last day and I need water, bid everything
    if day_context['day'] == EPISODE_DAYS and my_status['hp'] < 10:
        final_bid = my_status['budget']
    else:
        final_bid = min(my_status['budget'], current_bid)

    # Ensure bid is not negative
    final_bid = max(0.0, final_bid)
    
    # If budget is very low but I need water, try to bid whatever is left to survive
    # This handles cases where 'current_bid' might be high but budget is low
    if my_status['budget'] > 0 and final_bid < DAILY_SALARY * 0.1 and my_status['hp'] < 10:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.1)

    return final_bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    EPISODE_DAYS = 10
    WATER_REQ = 13
    DAILY_SALARY = 150

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, 1.0) if my_budget > 0 else 0.0

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    base_bid_percentage = 0.6
    
    if my_hp <= 2:
        base_bid_percentage = 1.1
    elif my_hp <= 4:
        base_bid_percentage = 0.9
    elif my_no_water_days > 0:
        base_bid_percentage = max(base_bid_percentage, 0.75)
    
    my_calculated_bid = DAILY_SALARY * base_bid_percentage

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        
        if my_hp <= 2:
            my_calculated_bid = max(my_calculated_bid, max_prev_bid + 10.0)
        elif my_hp <= 4:
            my_calculated_bid = max(my_calculated_bid, max_prev_bid + 5.0)
        else:
            my_calculated_bid = max(my_calculated_bid, max_prev_bid + 2.0)
        
        my_calculated_bid = max(my_calculated_bid, DAILY_SALARY * 0.4)
    
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_hp > 0:
        my_calculated_bid = max(my_calculated_bid, DAILY_SALARY * 1.0)
    
    final_bid = min(my_budget, my_calculated_bid)

    if my_budget > 0:
        final_bid = max(final_bid, 1.0)
    else:
        final_bid = 0.0

    return final_bid
"""
