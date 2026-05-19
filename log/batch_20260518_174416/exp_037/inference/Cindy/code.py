# ============================================================
# Experiment: exp_037
# Agent: Cindy
# Source: exp_037
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQ = 13
    MY_DAILY_SALARY = 150
    EPISODE_DAYS = 10 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # 1. Survival mode: If HP is very low or no water for a day
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        # Bid very aggressively to survive
        return min(my_status['budget'], MY_DAILY_SALARY * 0.95)

    # 2. No opponents: Bid minimal to get water
    if not alive_opponents:
        return min(my_status['budget'], MY_DAILY_SALARY * 0.2)

    # 3. Normal Play with Opponents
    base_bid = MY_DAILY_SALARY * 0.5 

    # Calculate total water demand
    total_demand = MY_WATER_REQ
    for opp in alive_opponents:
        total_demand += opp['water_requirement']

    # Adjust bid based on supply scarcity
    current_supply = day_context['supply']
    if current_supply < total_demand:
        # Water is scarce, increase bid
        scarcity_ratio = (total_demand - current_supply) / total_demand
        base_bid += base_bid * scarcity_ratio * 0.6 

    # Adjust bid based on yesterday's opponent bids
    yesterday_opponent_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_opponent_bids.append(prev_trace['bid'])

    if yesterday_opponent_bids:
        max_yesterday_bid = max(yesterday_opponent_bids)
        # If yesterday's highest bid was significant, ensure we are competitive
        if max_yesterday_bid > base_bid * 0.8: 
             base_bid = max(base_bid, max_yesterday_bid + 1)

    # Adjust for my current HP: if HP is declining, be more aggressive
    if my_status['hp'] <= 4: 
        base_bid = max(base_bid, MY_DAILY_SALARY * 0.7) 

    # Adjust for end-game: if it's nearing the end, be more aggressive if needed
    if day_context['day'] >= EPISODE_DAYS - 2: 
        if my_status['hp'] <= 5: 
             base_bid = max(base_bid, MY_DAILY_SALARY * 0.85)

    # Final bid constraints
    final_bid = min(my_status['budget'], base_bid)
    final_bid = max(final_bid, 15) 

    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    # Only one agent can get their full water requirement (13 units) given supply_range [15, 25].
    # This means direct competition for the single water slot.
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    # Base bid, adjusted by my health
    my_bid = DAILY_SALARY * 0.5 
    if my_status['no_water_days'] > 0 or my_status['hp'] <= 3:
        my_bid = DAILY_SALARY * 0.95 
    elif my_status['hp'] <= 5:
        my_bid = DAILY_SALARY * 0.8 

    # --- Opponent Analysis --- 
    alex_prev_bid = 0.0
    eric_prev_bid = 0.0
    alex_is_alive = False
    eric_is_alive = False

    for agent_id, opp in opponents_status.items():
        if opp['alive']:
            prev_trace = opp.get('previous_trace', {})
            if agent_id == "Alex":
                alex_is_alive = True
                if prev_trace and prev_trace.get('bid') is not None:
                    alex_prev_bid = prev_trace['bid']
                else:
                    # Default if no trace, based on meta-round context
                    alex_prev_bid = DAILY_SALARY * 0.85 
            elif agent_id == "Eric":
                eric_is_alive = True
                if prev_trace and prev_trace.get('bid') is not None:
                    eric_prev_bid = prev_trace['bid']
                else:
                    # Default if no trace, based on meta-round context
                    eric_prev_bid = DAILY_SALARY * 0.35 

    # Determine the target bid to beat for the single water slot
    target_bid_to_beat = 0.0
    
    if alex_is_alive:
        # Alex is the primary competitor. We need to beat Alex.
        target_bid_to_beat = alex_prev_bid
    elif eric_is_alive:
        # If Alex is not alive, Eric is the next competitor.
        target_bid_to_beat = eric_prev_bid
    
    # Adjust my bid to slightly exceed the target, if a target exists
    if target_bid_to_beat > 0:
        my_bid = max(my_bid, target_bid_to_beat + 1.0)

    # Ensure bid does not exceed budget
    my_bid = min(my_status['budget'], my_bid)
    
    # Ensure bid is at least 1.0 to win if uncontested
    my_bid = max(1.0, my_bid)
    
    return my_bid
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
    num_alive_opponents = len(alive_opponents)

    base_bid_value = DAILY_SALARY * 0.6

    highest_prev_bid = 0.0
    previous_bids_exist = False
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])
            previous_bids_exist = True

    if not previous_bids_exist:
        highest_prev_bid = base_bid_value 

    available_funds = my_status['budget'] + DAILY_SALARY

    my_bid = 0.0
    current_day = day_context['day']

    hp_factor = 1.0
    day_factor = 1.0

    if my_status['hp'] <= 2: 
        hp_factor = 1.3
    elif my_status['hp'] <= 5: 
        hp_factor = 1.15
    elif my_status['hp'] <= 8: 
        hp_factor = 1.0
    else: 
        hp_factor = 0.85

    if current_day >= EPISODE_DAYS - 2: 
        day_factor = 1.2
    elif current_day >= EPISODE_DAYS - 4: 
        day_factor = 1.1

    if highest_prev_bid > DAILY_SALARY * 0.8: 
        my_bid = highest_prev_bid + (DAILY_SALARY * 0.05 * hp_factor * day_factor)
    elif highest_prev_bid > DAILY_SALARY * 0.5: 
        my_bid = highest_prev_bid + (DAILY_SALARY * 0.02 * hp_factor * day_factor)
    else: 
        my_bid = base_bid_value * hp_factor * day_factor

    my_bid = max(my_bid, DAILY_SALARY * 0.3)

    if num_alive_opponents == 0:
        my_bid = DAILY_SALARY * 0.1

    my_bid = min(my_bid, available_funds)
    my_bid = max(0.0, my_bid)

    return float(my_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
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

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        aggressive_threshold = DAILY_SALARY * 0.85
        
        if highest_prev_bid >= aggressive_threshold:
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            else:
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else:
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
    else:
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.55)
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

    # If no opponents, bid minimally to secure water and save budget.
    if not alive_opponents:
        return min(my_status['budget'], MY_DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid_amount = MY_DAILY_SALARY * 0.55 # Default bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # High pressure: Opponents bid very high yesterday (e.g., >= 127.5 for my 150 salary)
        if highest_prev_bid >= MY_DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # My HP is good, try to save a bit
                bid_amount = MY_DAILY_SALARY * 0.6 # Bid 90
            else: # My HP is low, must bid very high
                bid_amount = MY_DAILY_SALARY * 0.95 # Bid 142.5
        # Moderate pressure: Opponents bid moderately high yesterday (e.g., >= 105 for my 150 salary)
        elif highest_prev_bid >= MY_DAILY_SALARY * 0.7:
            if my_status['hp'] > 5: # My HP is good, can be slightly less aggressive
                bid_amount = max(MY_DAILY_SALARY * 0.55, highest_prev_bid + 2.0) # Min 82.5, or highest+2
            else: # My HP is moderate/low, be aggressive
                bid_amount = max(MY_DAILY_SALARY * 0.8, highest_prev_bid + 5.0) # Min 120, or highest+5
        # Low pressure: Opponents bid low yesterday
        else:
            if my_status['hp'] > 7: # My HP is very good, can be conservative
                bid_amount = MY_DAILY_SALARY * 0.45 # Bid 67.5
            else: # Moderate HP, still competitive but not overly aggressive
                bid_amount = max(MY_DAILY_SALARY * 0.5, highest_prev_bid + 1.5) # Min 75, or highest+1.5
    
    # Override: If my HP is critically low, always bid very high
    if my_status['hp'] <= 2:
        bid_amount = MY_DAILY_SALARY * 0.98 # Bid 147

    # End game strategy: Last 2 days, good budget, ensure survival
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['budget'] > MY_DAILY_SALARY * 2:
        bid_amount = max(bid_amount, MY_DAILY_SALARY * 0.95) # Ensure at least 142.5

    # Ensure bid is at least a reasonable minimum if there are opponents
    if alive_opponents:
        bid_amount = max(bid_amount, MY_WATER_REQ * 5.0) # e.g., 65

    # Final check: Ensure bid does not exceed budget and is positive
    final_bid = min(my_status['budget'], bid_amount)
    return max(0.0, final_bid)
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

    # Determine if there are enough water slots for everyone
    # Given supply_range [15, 25] and WATER_REQ 13, num_water_slots will almost always be 1.
    # So, this condition will mostly only trigger if 'not alive_opponents'.
    num_water_slots = int(day_context['supply'] // WATER_REQ)
    if not alive_opponents:
        # If no opponents, bid a minimal amount to secure water
        return min(my_status['budget'], DAILY_SALARY * 0.3)
    
    # In this specific challenge, num_water_slots is almost always 1.
    # So, we are always in a competitive scenario for a single slot.

    # Determine highest previous bid among active opponents
    highest_prev_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])
    
    # If no previous bids from opponents (e.g., Day 1), set a default competitive bid
    if highest_prev_bid == 0.0:
        highest_prev_bid = DAILY_SALARY * 0.5 # A reasonable starting point for competition

    # Calculate days left in the episode
    days_left = EPISODE_DAYS - day_context['day'] + 1

    # --- Bidding Strategy based on HP and game stage --- 

    # Critical HP (must win)
    if my_status['hp'] <= 2:
        # Bid very aggressively to secure water.
        # Consider opponent's max bids (Eric's max was 165.31).
        # Bid slightly above highest previous, with a strong floor.
        bid_amount = max(highest_prev_bid * 1.05, DAILY_SALARY * 0.95, 145.0) # Ensure a high floor
        return min(my_status['budget'], bid_amount)

    # Low HP (need water soon)
    elif my_status['hp'] <= 5:
        # Need to be competitive, but can't afford to overspend recklessly if budget is tight.
        # Bid above average, but not desperate.
        bid_amount = max(highest_prev_bid + 5, DAILY_SALARY * 0.8)
        return min(my_status['budget'], bid_amount)

    # Healthy HP
    else:
        # If it's late in the game, become more aggressive even with healthy HP
        if days_left <= 3: # Last 3 days (e.g., Day 8, 9, 10 for EPISODE_DAYS=10)
            bid_amount = max(highest_prev_bid + 3, DAILY_SALARY * 0.85)
            return min(my_status['budget'], bid_amount)
        
        # Early/Mid game with healthy HP
        else:
            # Try to win water, but also conserve budget.
            # If opponents are bidding very high, consider letting them win to save budget,
            # especially if my HP is very good and I have many days left to recover.
            if highest_prev_bid > DAILY_SALARY * 0.9: # Opponents are very aggressive (>135)
                # If I have a good HP buffer, I can afford to lose a day to save budget.
                # Bid lower to test if they will overspend.
                bid_amount = DAILY_SALARY * 0.75 # Still competitive, but not escalating
            else:
                # Opponents are not extremely aggressive, bid competitively but with a margin.
                bid_amount = max(DAILY_SALARY * 0.6, highest_prev_bid + 2)
            
            return min(my_status['budget'], bid_amount)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_players = len(alive_opponents) + 1 # Including Cindy

    # Base bid: a safe starting point, aiming for profit but ensuring some water.
    # Roughly 65% of daily salary.
    base_bid = DAILY_SALARY * 0.65 
    
    current_bid = base_bid

    # --- Phase 1: Survival Mode (High Priority) ---
    # If HP is critically low, bid very aggressively to survive.
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95) 

    # --- Phase 2: React to Yesterday's Competition ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    # If opponents bid significantly yesterday, slightly outbid the highest to secure water.
    # Ensure we don't drop below base_bid even if max_yesterday_bid was low.
    if max_yesterday_bid > 0:
        current_bid = max(current_bid, max_yesterday_bid + 1.5)

    # --- Phase 3: Adjust based on Supply & Demand ---
    total_water_needed_by_players = num_alive_players * WATER_REQ
    supply = day_context['supply']

    # If supply is scarce (less than total needed), increase bid aggressively.
    if supply < total_water_needed_by_players:
        current_bid = max(current_bid, DAILY_SALARY * 0.8) 
        if my_status['hp'] <= 4:
             current_bid = max(current_bid, DAILY_SALARY * 0.9)
    # If supply is abundant (significantly more than needed), try to get water cheaper.
    elif supply >= total_water_needed_by_players + WATER_REQ * num_alive_players:
        current_bid = min(current_bid, DAILY_SALARY * 0.55)

    # --- Phase 4: Budget Management ---
    # Never bid more than current budget.
    final_bid = min(my_status['budget'], current_bid)
    
    # Ensure a minimum bid if budget allows, to stay competitive on low-bid days.
    if final_bid < DAILY_SALARY * 0.1 and my_status['budget'] >= DAILY_SALARY * 0.1:
        final_bid = max(final_bid, DAILY_SALARY * 0.1)
    
    # Ensure bid is at least 1 if budget allows, to not accidentally bid 0.
    if final_bid <= 0 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], 1.0)

    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    # Constants for bid thresholds
    CRITICAL_HP_THRESHOLD = 3
    LOW_HP_THRESHOLD = 6
    CONSERVATIVE_BID_PERCENT = 0.55
    NORMAL_BID_PERCENT = 0.65
    URGENT_BID_PERCENT = 0.8
    DESPERATE_BID_PERCENT = 0.95
    MAX_BID_CAP_PERCENT = 0.98 # Cap to avoid bidding full salary unless absolutely necessary

    # Initialize bid
    bid = DAILY_SALARY * CONSERVATIVE_BID_PERCENT

    # Step 1: Adjust bid based on my HP
    if my_status['hp'] <= CRITICAL_HP_THRESHOLD:
        bid = DAILY_SALARY * DESPERATE_BID_PERCENT
    elif my_status['hp'] <= LOW_HP_THRESHOLD:
        bid = DAILY_SALARY * URGENT_BID_PERCENT
    else:
        bid = DAILY_SALARY * NORMAL_BID_PERCENT # Healthy HP

    # Step 2: Adjust bid based on supply scarcity and number of competitors
    supply = day_context['supply']
    num_alive_opponents = len([o for o in opponents_status.values() if o['alive']])
    num_competitors = num_alive_opponents + 1 # Including myself

    # Calculate how many players can satisfy their water requirement
    num_possible_winners = int(supply // WATER_REQ) # CRITICAL INDEX RULE: int() conversion

    if supply < WATER_REQ: # Extremely low supply, impossible to get full water_req
        return min(my_status['budget'], DAILY_SALARY * 0.1) # Bid very low to conserve
    
    if num_possible_winners < num_competitors: # Water is scarce, some will miss out
        if num_possible_winners == 1: # Only one winner possible (highly competitive)
            # If I'm desperate, bid very high to try to be that one winner
            if my_status['hp'] <= CRITICAL_HP_THRESHOLD:
                bid = max(bid, DAILY_SALARY * DESPERATE_BID_PERCENT)
            elif my_status['hp'] <= LOW_HP_THRESHOLD:
                bid = max(bid, DAILY_SALARY * URGENT_BID_PERCENT + (DAILY_SALARY * 0.1)) # Even more urgent
            else:
                bid = max(bid, DAILY_SALARY * NORMAL_BID_PERCENT + (DAILY_SALARY * 0.1)) # Increase if healthy too
        else: # Some will miss out, but more than one can win
            if my_status['hp'] <= CRITICAL_HP_THRESHOLD:
                bid = max(bid, DAILY_SALARY * DESPERATE_BID_PERCENT)
            elif my_status['hp'] <= LOW_HP_THRESHOLD:
                bid = max(bid, DAILY_SALARY * URGENT_BID_PERCENT)
            else:
                bid = max(bid, DAILY_SALARY * NORMAL_BID_PERCENT) # Keep normal competitive bid

    else: # num_possible_winners >= num_competitors: Enough water for everyone
        # If everyone can get water, we can afford to be less aggressive, unless HP is low.
        if my_status['hp'] <= CRITICAL_HP_THRESHOLD:
            bid = max(bid, DAILY_SALARY * DESPERATE_BID_PERCENT) # Still desperate
        elif my_status['hp'] <= LOW_HP_THRESHOLD:
            bid = max(bid, DAILY_SALARY * URGENT_BID_PERCENT) # Still urgent
        else:
            bid = min(bid, DAILY_SALARY * CONSERVATIVE_BID_PERCENT) # Conserve if healthy and enough water for all

    # Step 3: Adjust bid based on opponent's previous bids (yesterday's trace)
    # Identify strong opponents from the LATEST METAROUND CONTEXT
    # Alex, David, Eric seem to be the strongest bidders based on max_bid and average_bid.
    strong_opponent_ids = ["Alex", "David", "Eric"]
    highest_yesterday_strong_bid = 0.0

    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive'] and opp_id in strong_opponent_ids:
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                highest_yesterday_strong_bid = max(highest_yesterday_strong_bid, prev['bid'])

    if highest_yesterday_strong_bid > 0:
        # If strong opponents bid high yesterday, I need to be competitive
        # Add a small buffer to try and outbid them
        if my_status['hp'] <= CRITICAL_HP_THRESHOLD:
            bid = max(bid, highest_yesterday_strong_bid + (DAILY_SALARY * 0.1)) # More aggressive if desperate
        elif my_status['hp'] <= LOW_HP_THRESHOLD:
            bid = max(bid, highest_yesterday_strong_bid + (DAILY_SALARY * 0.05))
        else:
            # If healthy, try to outbid but don't overspend if not necessary
            # Only increase if my current bid is lower than their previous high bid + a small margin
            if bid < highest_yesterday_strong_bid + 5:
                bid = highest_yesterday_strong_bid + 5

    # Final checks and constraints
    final_bid = min(my_status['budget'], bid) # Cannot bid more than budget
    final_bid = max(1.0, final_bid) # Bid must be positive

    # Cap the bid to avoid overspending too much, unless budget is critically low
    # and I need to bid high to survive.
    if my_status['hp'] > CRITICAL_HP_THRESHOLD:
        final_bid = min(final_bid, DAILY_SALARY * MAX_BID_CAP_PERCENT)
    else: # If desperate, allow bidding up to current budget, but still apply a high cap relative to salary
        final_bid = min(final_bid, my_status['budget'], DAILY_SALARY * 1.2) # Allow slightly over salary if desperate and budget allows

    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no alive opponents, bid a minimal amount to ensure water and conserve budget
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.2) # 30

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    bid = 0
    # Desperate state: very low HP or already missed water
    if my_hp <= 2 or my_no_water_days >= 1:
        bid = DAILY_SALARY * 0.98 # 147 - Very aggressive to ensure survival
    # High HP, but getting low, need to be aggressive
    elif my_hp <= 4:
        bid = DAILY_SALARY * 0.95 # 142.5
    else: # Stable HP, but competition is always high given supply constraints (only one winner possible)
        if highest_prev_bid > 0:
            # Try to outbid the strongest opponent from yesterday
            bid = highest_prev_bid + 2.5 # Add a small margin to win
        else:
            # Default strong bid if no previous bids (e.g., first day or opponents changed)
            bid = DAILY_SALARY * 0.85 # 127.5 - A strong competitive bid

    # Ensure bid is at least a minimum to be competitive
    bid = max(bid, DAILY_SALARY * 0.7) # Minimum competitive bid of 105

    # Ensure bid does not exceed available budget
    return min(my_budget, bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    supply = day_context['supply']
    num_alive_agents = len(alive_opponents) + 1 

    if my_hp <= 2:
        return min(my_budget, DAILY_SALARY * 0.95)
    if my_hp <= 5:
        return min(my_budget, DAILY_SALARY * 0.85)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    base_bid = DAILY_SALARY * 0.6 

    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_hp > 7 and current_day < EPISODE_DAYS - 2:
                base_bid = max(base_bid, highest_prev_bid * 0.95)
            else:
                base_bid = max(base_bid, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            base_bid = max(base_bid, highest_prev_bid + 2)
        else:
            base_bid = max(base_bid, highest_prev_bid + 1)

    if supply < num_alive_agents * WATER_REQ * 0.6:
        base_bid = max(base_bid, DAILY_SALARY * 0.7)
    elif supply < num_alive_agents * WATER_REQ * 0.4:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    days_left = EPISODE_DAYS - current_day + 1
    if days_left <= 3:
        if my_hp <= 7:
            base_bid = max(base_bid, DAILY_SALARY * 0.9)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.75)
    
    final_bid = min(my_budget, base_bid)
    
    final_bid = max(final_bid, DAILY_SALARY * 0.05) 

    return final_bid
"""
