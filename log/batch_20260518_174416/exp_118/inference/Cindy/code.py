# ============================================================
# Experiment: exp_118
# Agent: Cindy
# Source: exp_118
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents left, bid minimally to secure water and save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.05) 

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine competition level based on supply and number of active players
    supply = day_context['supply']
    num_possible_winners = int(supply // WATER_REQ)
    num_active_players = len(alive_opponents) + 1 # Myself + alive opponents

    # Scenario 1: Enough water for everyone (or more) - try to bid low
    if num_possible_winners >= num_active_players:
        if my_status['hp'] <= 3: # Still a bit cautious if HP is not great
            return min(my_status['budget'], DAILY_SALARY * 0.25)
        # Otherwise, bid very conservatively low
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Scenario 2: Water is scarce (num_possible_winners < num_active_players)
    # 1. My desperation takes priority
    if my_status['hp'] <= 2: # Critical HP
        return min(my_status['budget'], DAILY_SALARY * 0.95) # Bid very high to survive
    if my_status['hp'] <= 4: # Low HP
        return min(my_status['budget'], DAILY_SALARY * 0.75) # Bid high

    # 2. React to opponent's previous bids if water is scarce and I'm not critically desperate
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If previous bids were very high, opponents are aggressive
        if highest_prev_bid >= DAILY_SALARY * 0.8: 
            if my_status['hp'] > 5: # Good HP, try to win but don't overspend too much
                return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1))
            else: # My HP is okay, but not critical, still need water
                return min(my_status['budget'], DAILY_SALARY * 0.85) # Bid high

        # If previous bids were moderate, bid slightly above to win
        if highest_prev_bid >= DAILY_SALARY * 0.4:
            return min(my_status['budget'], highest_prev_bid + 1)

        # If previous bids were low, bid moderately to win
        return min(my_status['budget'], DAILY_SALARY * 0.45) 

    # Default bid if no previous bids (e.g., Day 1) and water is scarce, and I'm not desperate
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid = DAILY_SALARY * 0.55 # Default bid for healthy state, if no specific conditions met

    if not yesterday_bids:
        # No previous bids from opponents (e.g., Day 1 of the meta-round)
        if my_status['hp'] <= 2:
            bid = DAILY_SALARY * 0.9 # Critical HP, bid aggressively
        else:
            bid = DAILY_SALARY * 0.55 # Healthy HP, moderate bid
    else:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # Opponents are bidding very high, indicating fierce competition
            if my_status['hp'] > 3:
                # If my HP is good, try to save money by bidding lower
                bid = DAILY_SALARY * 0.3
            else:
                # If my HP is low, I must bid very aggressively to survive
                bid = DAILY_SALARY * 0.95
        else:
            # Opponents are bidding moderately or low
            # Bid slightly above the highest previous bid, with a floor of DAILY_SALARY * 0.5
            bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)

    # Ensure bid does not exceed available budget and is non-negative
    final_bid = min(my_status['budget'], bid)
    final_bid = max(0.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
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

        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 4:
                return min(my_status['budget'], max(DAILY_SALARY * 0.6, highest_prev_bid + 1.0))
            else:
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            if my_status['hp'] <= 3:
                return min(my_status['budget'], max(DAILY_SALARY * 0.85, highest_prev_bid + 1.5))
            else:
                return min(my_status['budget'], max(DAILY_SALARY * 0.7, highest_prev_bid + 1.0))
        
        else:
            if my_status['hp'] <= 2:
                return min(my_status['budget'], DAILY_SALARY * 0.9)
            elif my_status['hp'] <= 5:
                return min(my_status['budget'], max(DAILY_SALARY * 0.65, highest_prev_bid + 0.5))
            else:
                return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 0.1))
    
    else:
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        elif my_status['hp'] <= 5:
            return min(my_status['budget'], DAILY_SALARY * 0.7)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no active opponents, bid conservatively to maintain budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid based on opponent behavior and game state
    base_bid = DAILY_SALARY * 0.6 # Default moderate bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were bidding high, we need to be competitive
        if highest_prev_bid >= DAILY_SALARY * 0.8: # High pressure threshold
            if my_status['hp'] > 3: # If HP is good, bid slightly less aggressively to save budget
                base_bid = max(base_bid, highest_prev_bid + 2) # Try to outbid by a small margin
            else: # If HP is low, bid very aggressively
                base_bid = max(base_bid, DAILY_SALARY * 0.95)
        else: # Opponents were not bidding extremely high, try to outbid them by a slightly larger margin
            base_bid = max(base_bid, highest_prev_bid + 5)
    
    # Adjust bid based on my current HP
    if my_status['hp'] <= 2: # Critical HP, bid very high
        base_bid = max(base_bid, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4: # Low HP
        base_bid = max(base_bid, DAILY_SALARY * 0.85)
    elif my_status['hp'] >= 8: # High HP, can be slightly less aggressive but still aim to win
        base_bid = max(base_bid, DAILY_SALARY * 0.7)
    
    # Adjust bid based on day (increasing pressure towards the end of the meta-round)
    day_progress_factor = 1 + (day_context['day'] / EPISODE_DAYS) * 0.15 # Up to 15% increase by last day
    base_bid *= day_progress_factor

    # Final bid must be within budget and non-negative
    final_bid = min(my_status['budget'], base_bid)
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        # If no opponents, bid minimally to get water
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Base bid: a portion of daily salary
    base_bid = DAILY_SALARY * 0.6 # Starting at 90

    # Adjust bid based on my HP and no_water_days for urgency
    if my_status['no_water_days'] > 0 or my_status['hp'] <= 3:
        # Urgent need for water
        base_bid = DAILY_SALARY * 0.9 # 135
    if my_status['hp'] <= 1:
        # Critical situation, bid very high
        base_bid = DAILY_SALARY * 1.2 # 180 (up to budget)

    # Adjust based on day progress (become more aggressive late game)
    current_day = day_context['day']
    if current_day >= EPISODE_DAYS * 0.7: # Last 30% of days (Day 7 onwards for 10 days)
        base_bid *= 1.1 # Increase bid by 10%

    # Adjust based on supply scarcity
    # If supply is low, competition is higher. Lower third of supply range (15-18.33)
    if day_context['supply'] <= MIN_SUPPLY + (MAX_SUPPLY - MIN_SUPPLY) / 3:
        base_bid *= 1.15 # Increase bid by 15%

    # Analyze opponent's previous bids to react
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_bid = base_bid # Start with my calculated base bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If opponents were very aggressive yesterday (e.g., bid >= 80% of daily salary)
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 3: # If I'm not in critical condition, consider backing off slightly to save budget
                # Back off, but not too much, ensure it's still competitive if others also back off
                current_bid = max(current_bid * 0.8, highest_prev_bid * 0.7)
                current_bid = max(current_bid, DAILY_SALARY * 0.4) # Ensure a minimum competitive bid
            else: # If HP is low, I must get water, try to outbid
                current_bid = max(current_bid, highest_prev_bid * 1.05) # Bid slightly above
        else:
            # Opponents were not extremely aggressive, try to slightly outbid to secure water
            current_bid = max(current_bid, highest_prev_bid + 5) # Bid slightly above highest previous bid
    
    # Ensure bid doesn't exceed budget
    final_bid = min(my_status['budget'], current_bid)

    # Ensure bid is at least 1 to avoid zero bids
    final_bid = max(1.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    days_left = EPISODE_DAYS - day_context['day']

    # Critical Health / No Water Days Logic: Bid aggressively to survive
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        return min(my_status['budget'], DAILY_SALARY * 1.5)

    # Collect Yesterday's Bids from Opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine Base Bid
    if not yesterday_bids:
        # Default competitive bid if no previous bids or all were very low
        base_bid = DAILY_SALARY * 0.8
    else:
        highest_prev_bid = max(yesterday_bids)
        base_bid = max(DAILY_SALARY * 0.7, highest_prev_bid + 1)

    # Adjust Bid based on Supply
    current_supply = day_context['supply']
    if current_supply <= MIN_SUPPLY + WATER_REQ // 2:
        # Supply is tight, increase bid
        base_bid *= 1.15
    elif current_supply >= MAX_SUPPLY - WATER_REQ // 2:
        # Supply is abundant, decrease bid to save money
        base_bid *= 0.9

    # Adjust Bid based on My HP and Days Left
    final_bid = base_bid
    if my_status['hp'] > 7 and days_left > EPISODE_DAYS / 2:
        # Healthy and early/mid game, try to save money
        final_bid = max(DAILY_SALARY * 0.5, final_bid * 0.9)
    elif my_status['hp'] > 4 or days_left <= EPISODE_DAYS / 2:
        # Moderately healthy or late game, be more competitive
        final_bid = max(DAILY_SALARY * 0.7, final_bid * 1.05)
    else:
        # HP is somewhat low (but not critical yet), be aggressive
        final_bid = max(DAILY_SALARY * 0.9, final_bid * 1.1)

    # Final Bid Constraints
    final_bid = max(0.0, final_bid)
    final_bid = min(final_bid, my_status['budget'])
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

    # If no opponents, bid minimum to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Calculate days left to manage budget
    days_left = EPISODE_DAYS - day_context['day'] + 1
    
    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid strategy
    # If HP is critical or no water days accumulating, bid aggressively
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        # Desperate for water, bid high
        bid = DAILY_SALARY * 0.95 
        if highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid + 5) 
    else:
        # HP is healthy, can be more strategic
        # If it's late in the game, increase aggression
        if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days
            bid = DAILY_SALARY * 0.8 
            if highest_prev_bid > 0:
                bid = max(bid, highest_prev_bid + 2) 
        else:
            # Early to mid-game, balance conservation and competition
            if highest_prev_bid > 0:
                if highest_prev_bid > DAILY_SALARY * 1.0: # Opponent bid very high (like Alex's max bid history)
                    # If my budget is tight, I might not compete at this level
                    if my_status['budget'] / days_left < DAILY_SALARY * 0.8: 
                        bid = DAILY_SALARY * 0.5 
                    else:
                        bid = highest_prev_bid + 1 
                else: # Moderate highest_prev_bid
                    bid = max(DAILY_SALARY * 0.6, highest_prev_bid + 5) 
            else:
                # No previous bids, or all were 0. Bid a reasonable amount.
                bid = DAILY_SALARY * 0.6 

    # Ensure bid does not exceed available budget
    final_bid = min(my_status['budget'], bid)
    
    # Ensure bid is at least 1 if budget allows, to signal intent
    if final_bid == 0 and my_status['budget'] > 0:
        final_bid = 1

    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid conservatively to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # High pressure scenario: If highest previous bid was very high
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # If I have good HP, I can try to save or even skip a day
                return min(my_status['budget'], DAILY_SALARY * 0.35)
            # If HP is low (<=3), I am desperate
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        
        # Moderate pressure scenario: Try to outbid slightly
        return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 2.0))

    # Default bids if no previous bids are available (e.g., Day 1)
    if my_status['hp'] <= 2: # Very low HP, bid aggressively
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    
    # Default moderate bid
    return min(my_status['budget'], DAILY_SALARY * 0.55)
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

    # If no opponents, bid very low to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Get yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0 # Ensure float for consistent math

    # Calculate remaining days
    remaining_days = EPISODE_DAYS - day_context['day']

    # --- Bidding Logic ---

    # 1. Desperation: Low HP or multiple days without water
    # Prioritize survival if HP is critical or missed water recently
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        # Bid very aggressively, aiming to outbid the highest opponent from yesterday
        return min(my_status['budget'], max(DAILY_SALARY * 0.95, highest_prev_bid + 1.5))

    # 2. End game aggression: If few days left, be more aggressive
    if remaining_days <= 3:
        # Increase bid to ensure water, considering opponent's past bids
        return min(my_status['budget'], max(DAILY_SALARY * 0.8, highest_prev_bid + 1.5))

    # 3. Normal / Mid-game strategy
    # Assess competition based on supply vs. total water needed (including self)
    total_water_needed_by_active_plus_me = WATER_REQ + sum(o['water_requirement'] for o in alive_opponents)

    # If supply is tight, competition is high
    if day_context['supply'] < total_water_needed_by_active_plus_me:
        # If opponents were bidding high yesterday, respond with a slightly higher bid
        if highest_prev_bid >= DAILY_SALARY * 0.7:
            return min(my_status['budget'], highest_prev_bid + 1.5)
        # Otherwise, a strong but not desperate bid
        return min(my_status['budget'], DAILY_SALARY * 0.7)
    
    # If supply is relatively abundant
    else:
        # If opponents were bidding somewhat high, bid slightly above them to win cheaply
        if highest_prev_bid >= DAILY_SALARY * 0.5:
            return min(my_status['budget'], highest_prev_bid + 1.5)
        # If opponents were bidding low, or no strong signal, bid conservatively
        return min(my_status['budget'], DAILY_SALARY * 0.45)

    # Fallback (should not be reached)
    return min(my_status['budget'], DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    EPISODE_DAYS = 10 

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    is_critical_state = (my_hp <= 2) or (my_no_water_days >= 1)

    highest_prev_bid = 0.0
    eric_prev_bid = 0.0
    
    alive_opponents_count = 0
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            alive_opponents_count += 1
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                bid = prev_trace['bid']
                highest_prev_bid = max(highest_prev_bid, bid)
                if opp_id == "Eric":
                    eric_prev_bid = bid

    if alive_opponents_count == 0:
        return min(my_budget, DAILY_SALARY * 0.4)

    bid_to_beat = 0.0
    if eric_prev_bid > 0:
        bid_to_beat = eric_prev_bid
    else:
        bid_to_beat = highest_prev_bid

    target_bid = 0.0
    if is_critical_state:
        target_bid = bid_to_beat + 5.0
        target_bid = max(target_bid, DAILY_SALARY * 0.8)
    else:
        target_bid = bid_to_beat + 1.0
        target_bid = max(target_bid, DAILY_SALARY * 0.5)

    final_bid = min(my_budget, DAILY_SALARY * 0.95, target_bid)
    
    return max(1.0, final_bid)
"""
