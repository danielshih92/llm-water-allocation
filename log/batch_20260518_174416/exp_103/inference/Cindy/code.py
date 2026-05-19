# ============================================================
# Experiment: exp_103
# Agent: Cindy
# Source: exp_103
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    current_supply = day_context['supply']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to get water (only one water available, so I'll get it)
    if not alive_opponents:
        return min(my_current_budget, DAILY_SALARY * 0.1)

    # In this scenario, given supply_range [15,25] and WATER_REQ 13,
    # only one agent can ever get water per day. Competition is always for the single water unit.

    max_prev_opponent_bid = 0
    desperate_opponents_count = 0
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            # Opponent is desperate if low HP or missed water yesterday
            if opp_data['hp'] <= 2 or opp_data['no_water_days'] >= 1:
                desperate_opponents_count += 1
            
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                max_prev_opponent_bid = max(max_prev_opponent_bid, prev_trace['bid'])

    # Base bid strategy for a highly competitive, single-winner scenario
    # Start high, as only one can win
    bid = DAILY_SALARY * 0.7 

    # Adjust bid based on my HP
    if my_current_hp <= 1: # Critical HP, must win
        bid = DAILY_SALARY * 0.99
    elif my_current_hp == 2: # Very low HP, high priority to win
        bid = DAILY_SALARY * 0.95
    elif my_current_hp == 3: # Moderate HP, still need to win consistently
        bid = DAILY_SALARY * 0.85
    else: # Healthy HP, can be slightly less aggressive but still aim to win
        bid = DAILY_SALARY * 0.75

    # Exploit previous_trace: If opponents bid high yesterday, expect them to continue
    if max_prev_opponent_bid > 0:
        # If I'm under pressure (low HP) or opponents are desperate, bid significantly above their max previous bid
        if my_current_hp <= 3 or desperate_opponents_count > 0:
            bid = max(bid, max_prev_opponent_bid + 10) # Add a larger buffer to secure win
        else:
            # If I'm healthy, but opponents bid high, still need to outbid
            bid = max(bid, max_prev_opponent_bid * 1.1) # Bid 10% higher than previous max
    else: # No previous bids or all were 0, implies early game or very low competition initially
        # If no previous bids, and opponents are desperate, assume they'll bid high
        if desperate_opponents_count > 0:
            bid = max(bid, DAILY_SALARY * 0.8) # Expect high bids from desperate opponents

    # Adjust for end of game: as day progresses, value of water increases, especially if I'm not at max HP
    # Max HP is EPISODE_DAYS (10).
    if current_day >= EPISODE_DAYS - 2 and my_current_hp < EPISODE_DAYS: # Last 2 days
        if my_current_hp <= 3:
            bid = max(bid, DAILY_SALARY * 0.99) # Bid almost full salary to survive
        else:
            bid = max(bid, DAILY_SALARY * 0.85) # Still very aggressive to finish strong

    # Ensure bid does not exceed budget and is non-negative
    final_bid = min(my_current_budget, bid)
    final_bid = max(0, final_bid)
    
    # Ensure bid is at least a minimum positive value if budget allows and not 0 HP
    if final_bid == 0 and my_current_budget > 0 and my_current_hp > 0:
        final_bid = 1 # Always try to bid something if possible to avoid losing by default

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

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    # Emergency bidding: If HP is low or I missed water yesterday
    if my_current_hp <= 2 or my_status['no_water_days'] > 0:
        return min(my_current_budget, DAILY_SALARY * 0.95) # Bid aggressively to survive

    # Identify alive opponents and gather their previous bids
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # Base bid calculation
    base_bid = DAILY_SALARY * 0.55 # A moderate starting point

    # Adjust base bid based on yesterday's opponent bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If the highest previous bid was significant, consider bidding slightly above it
        if highest_prev_bid >= DAILY_SALARY * 0.5: # If opponents are bidding somewhat high
            base_bid = max(base_bid, highest_prev_bid + 1.0)
        else: # If opponents were bidding low, maintain a reasonable base but don't overbid
            base_bid = max(base_bid, highest_prev_bid * 1.1)
    
    # Adjust bid based on supply and number of competitors
    # How many full water requirements can be met by the current supply
    available_slots = int(current_supply // WATER_REQ)
    
    # If supply is tight (not enough for everyone + me)
    if available_slots < num_alive_opponents + 1:
        base_bid *= 1.2 # Increase bid due to high competition
    # If supply is abundant (enough for everyone + me + more)
    elif available_slots >= num_alive_opponents + 2:
        base_bid *= 0.8 # Decrease bid as competition is lower

    # Budget and end-game considerations
    days_left = EPISODE_DAYS - current_day
    
    # If we are nearing the end of the game and budget is high, we can afford to bid higher
    if days_left <= 3 and my_current_budget > DAILY_SALARY * 3:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    # If I have plenty of HP and it's early/mid game, conserve budget
    if my_current_hp >= 8 and current_day < EPISODE_DAYS / 2:
        base_bid = min(base_bid, DAILY_SALARY * 0.45) # Conserve if healthy and early

    # Ensure the bid is within reasonable bounds
    # Max bid should not exceed budget, and generally not too much more than daily salary
    # Min bid should be enough to win against passive players
    final_bid = min(my_current_budget, base_bid, DAILY_SALARY * 0.85) # Cap at 85% of daily salary normally
    final_bid = max(final_bid, DAILY_SALARY * 0.25) # Ensure a minimum bid to stay competitive

    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10
    MIN_SUPPLY = 15.0
    MAX_SUPPLY = 25.0

    # Base bid: a solid starting point
    base_bid = DAILY_SALARY * 0.6

    # --- Urgency based on my HP and no_water_days ---
    if my_status['no_water_days'] > 0:
        # Critical: I haven't gotten water recently, must bid aggressively.
        base_bid = DAILY_SALARY * 1.1
    elif my_status['hp'] <= 2:
        # Very low HP, desperate
        base_bid = DAILY_SALARY * 1.05
    elif my_status['hp'] <= 5:
        # Low HP, need to secure water
        base_bid = DAILY_SALARY * 0.85

    # --- Adjust bid based on supply ---
    # Normalize supply to a 0-1 range (0 for min supply, 1 for max supply)
    supply_normalized = (day_context['supply'] - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    # If supply is low (normalized close to 0), increase bid. If high (normalized close to 1), decrease bid.
    supply_adjustment = (1 - supply_normalized) * (DAILY_SALARY * 0.2) - supply_normalized * (DAILY_SALARY * 0.1)
    base_bid += supply_adjustment

    # --- Adjust bid based on opponent behavior (yesterday's trace) ---
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents were generally aggressive yesterday, especially if I'm urgent
        if max_yesterday_bid >= DAILY_SALARY * 0.8 or my_status['hp'] <= 5:
            base_bid = max(base_bid, max_yesterday_bid * 1.05) # Try to outbid the highest by a small margin
        elif avg_yesterday_bid >= DAILY_SALARY * 0.5:
             base_bid = max(base_bid, avg_yesterday_bid * 1.1) # Be slightly more aggressive than average
        else:
            # If opponents were generally passive, try to save money but still win
            base_bid = min(base_bid, avg_yesterday_bid * 1.2 + 5) # Bid a bit more than average, plus a small buffer

    # --- Adjust bid based on day of the episode ---
    if day_context['day'] > EPISODE_DAYS * 0.7: # Last 30% of the days
        if my_status['hp'] > 5: # If I'm doing well, maintain pressure, maybe slightly higher bid
            base_bid = max(base_bid, DAILY_SALARY * 0.75)
        else: # If I'm struggling late game, bid very aggressively
            base_bid = max(base_bid, DAILY_SALARY * 1.0)

    # Final bid cannot exceed current budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure a minimum bid if I desperately need water
    if my_status['no_water_days'] > 0 or my_status['hp'] <= 3:
        final_bid = max(final_bid, DAILY_SALARY * 0.4)

    # Ensure bid is always positive
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents are alive, bid minimally to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid based on my HP status
    # Aggressive if HP is very low
    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.95
    # Moderately aggressive if HP is low
    elif my_status['hp'] <= 5:
        base_bid = DAILY_SALARY * 0.75
    # Moderate if HP is good
    else:
        base_bid = DAILY_SALARY * 0.55

    # Adjust bid based on opponents' previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were bidding very high (e.g., > 80% of daily salary)
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 4: # Good HP, try to conserve but stay competitive
                # Bid slightly below the highest previous bid, but not lower than our base moderate bid
                calculated_bid = max(base_bid, highest_prev_bid * 0.85)
            else: # Low HP, must bid aggressively to survive
                calculated_bid = DAILY_SALARY * 0.98 
        # If opponents' previous bids were moderate
        else:
            # Bid slightly above the highest previous bid to win, but at least our base bid
            calculated_bid = max(base_bid, highest_prev_bid + 5.0)
    else:
        # No previous bids (e.g., Day 1 or no relevant opponent history), use the base bid
        calculated_bid = base_bid
    
    # Ensure bid does not exceed available budget
    final_bid = min(my_status['budget'], calculated_bid)
    
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # 1. Base bid calculation (percentage of daily salary)
    base_bid_percentage = 0.55 # Default moderate bid

    # Adjust based on my HP (primary driver)
    if my_hp <= 2: # Critical HP
        base_bid_percentage = 0.98 # Bid very aggressively, almost full salary
    elif my_hp <= 4: # Low HP
        base_bid_percentage = 0.85 # Bid aggressively
    elif my_hp <= 6: # Medium-low HP
        base_bid_percentage = 0.70
    elif my_hp <= 8: # Medium HP
        base_bid_percentage = 0.60
    # If HP is > 8, use the default 0.55

    # Adjust based on day progression (secondary driver)
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        base_bid_percentage = max(base_bid_percentage, 0.90)
    elif current_day >= EPISODE_DAYS - 4: # Last 4 days
        base_bid_percentage = max(base_bid_percentage, 0.75)

    base_bid = DAILY_SALARY * base_bid_percentage

    # 2. React to opponent's previous bids (competition factor)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponent was very aggressive
            base_bid = max(base_bid, min(DAILY_SALARY * 1.05, highest_prev_bid + 5))
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # Opponent was moderately aggressive
            base_bid = max(base_bid, highest_prev_bid + 2)

    # 3. Adjust for extreme budget situations
    if my_budget < DAILY_SALARY * 0.5 and my_hp > 4: # Low budget, but not critical HP
        base_bid = min(base_bid, my_budget * 0.8) # Try to save, don't bid everything
    elif my_budget > DAILY_SALARY * 3: # High budget, can afford to be more aggressive
        base_bid = base_bid * 1.05 # Slightly increase bid

    # Final check: Ensure bid does not exceed current budget
    final_bid = min(my_budget, base_bid)

    # Ensure a minimum bid if budget allows, to stay in contention
    if final_bid < 1.0 and my_budget > 0:
        final_bid = 1.0
    elif my_budget == 0:
        final_bid = 0.0

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

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to save budget
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid calculation - designed to be competitive for the single water slot
    base_bid = DAILY_SALARY * 0.75 

    # Adjust bid based on my status
    if my_hp <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95
    elif my_no_water_days >= 1: # Missed water yesterday
        base_bid = DAILY_SALARY * 0.9
    elif my_hp <= 5: # Low HP
        base_bid = DAILY_SALARY * 0.85

    # Adjust bid based on opponents' previous behavior
    if highest_prev_bid >= base_bid: # If opponents were bidding high or higher than my current base
        base_bid = highest_prev_bid + 5 # Try to slightly outbid them

    # Adjust bid based on competition intensity
    if num_alive_opponents > 2: # More opponents mean higher competition for the single slot
        base_bid += 10 

    # End game aggression
    if current_day >= EPISODE_DAYS - 2: # Last few days, prioritize survival
        base_bid = max(base_bid, DAILY_SALARY * 0.9) 

    # Ensure bid doesn't exceed budget and is at least a minimal positive value
    final_bid = min(my_budget, base_bid)
    final_bid = max(1.0, final_bid)

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

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.6

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)

        if max_yesterday_bid > DAILY_SALARY * 0.8:
            base_bid = min(DAILY_SALARY * 0.9, max_yesterday_bid + 5)
        elif max_yesterday_bid > DAILY_SALARY * 0.6:
            base_bid = max(DAILY_SALARY * 0.65, max_yesterday_bid + 1)
        else:
            base_bid = max(DAILY_SALARY * 0.4, avg_yesterday_bid * 0.9)

    current_bid = base_bid

    if my_status['hp'] <= 2:
        current_bid = max(current_bid, DAILY_SALARY * 0.95)
        if yesterday_bids:
            current_bid = max(current_bid, max_yesterday_bid + 10)
    elif my_status['no_water_days'] >= 1:
        current_bid = max(current_bid, DAILY_SALARY * 0.85)
        if yesterday_bids:
            current_bid = max(current_bid, max_yesterday_bid + 5)

    num_competitors_for_water = len(alive_opponents) + 1
    num_water_units_available_for_my_req = int(day_context['supply'] // WATER_REQ)

    if num_water_units_available_for_my_req < num_competitors_for_water:
        current_bid = max(current_bid, DAILY_SALARY * 0.75)
        if yesterday_bids:
            current_bid = max(current_bid, max_yesterday_bid + 7)
    elif num_water_units_available_for_my_req >= num_competitors_for_water + 1:
        current_bid = min(current_bid, DAILY_SALARY * 0.5)
        if yesterday_bids:
            current_bid = min(current_bid, avg_yesterday_bid * 0.9)

    final_bid = min(my_status['budget'], current_bid)

    if final_bid <= 0 and my_status['budget'] > 0:
        return min(my_status['budget'], 0.01)
    elif final_bid <= 0:
        return 0.0
    
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

    # If no opponents are alive, bid minimal to secure water and save budget
    if not alive_opponents:
        return max(1.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Initialize base bid based on my HP
    base_bid = 0.0
    if my_status['hp'] <= 2: # Critical HP
        base_bid = DAILY_SALARY * 1.2
    elif my_status['hp'] <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.95
    else: # High HP
        base_bid = DAILY_SALARY * 0.6

    # Adjust base bid based on day progress (end game pressure)
    current_day = day_context['day']
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 3 and my_status['hp'] <= 3: # Last few days, need to survive
        base_bid = max(base_bid, DAILY_SALARY * 1.3) # Bid very aggressively

    # Incorporate opponent's yesterday's highest bid
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponent bid high yesterday, I should try to beat it, especially if my HP is not high
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponent was aggressive
            if my_status['hp'] <= 4: # Need to win
                base_bid = max(base_bid, highest_prev_bid + 5) # Try to outbid
            else: # Can afford to be slightly less aggressive, but still competitive
                base_bid = max(base_bid, highest_prev_bid + 1)
        # If opponent bid low yesterday, try to win slightly above their bid if my HP is high
        elif highest_prev_bid < DAILY_SALARY * 0.5 and my_status['hp'] > 4: # Opponent was very passive AND I have high HP
            base_bid = min(base_bid, highest_prev_bid + 10) # Try to win cheaply, but ensure it's higher
        # If opponents were moderately aggressive (0.5 to 0.8 of salary)
        else:
            if my_status['hp'] <= 3: # Need to win
                base_bid = max(base_bid, highest_prev_bid + 3)
            else: # Can be slightly less aggressive
                base_bid = max(base_bid, highest_prev_bid + 1)

    # Final bid must be positive and not exceed current budget
    bid = max(1.0, min(my_status['budget'], base_bid))

    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_HP = 10
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid very low to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # Initialize a base bid, strong due to competitive "one winner" scenario
    base_bid = DAILY_SALARY * 0.8

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Very critical HP, about to die
        base_bid = DAILY_SALARY * 1.4
    elif my_status['hp'] == 3: # Critical HP
        base_bid = DAILY_SALARY * 1.1
    elif my_status['hp'] <= 5: # Medium-low HP
        base_bid = DAILY_SALARY * 0.9
    # If hp > 5, base_bid remains DAILY_SALARY * 0.8

    # Adjust bid based on yesterday's opponent bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If I'm low on HP, I need to be very aggressive to win water
        if my_status['hp'] <= 3:
            base_bid = max(base_bid, highest_prev_bid + 10) # Add a buffer to win
        elif my_status['hp'] <= 5: # Medium-low HP, still need water
            base_bid = max(base_bid, highest_prev_bid + 5)
        else: # Higher HP, can be slightly more conservative but still competitive
            base_bid = max(base_bid, highest_prev_bid * 0.95)
            # Ensure it's at least a decent amount if highest_prev_bid was low
            base_bid = max(base_bid, DAILY_SALARY * 0.7)

    # Adjust bid based on day - more desperate towards the end
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: # Last couple of days, survival is paramount
        if my_status['hp'] <= 5:
            base_bid = max(base_bid, my_status['budget'] * 0.9) # Use almost all budget if critical
        elif my_status['hp'] <= 7:
            base_bid = max(base_bid, my_status['budget'] * 0.7)
    elif remaining_days <= 4: # Mid-late game
        if my_status['hp'] <= 3:
            base_bid = max(base_bid, DAILY_SALARY * 1.2)

    # Final bid must not exceed current budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure a minimum bid to stay in contention, especially if I need water
    if my_status['hp'] <= 7: # If HP is not full, ensure I bid at least a certain amount
        final_bid = max(final_bid, DAILY_SALARY * 0.5)
    else: # If HP is high, can afford to bid lower if competition seems low
        final_bid = max(final_bid, DAILY_SALARY * 0.3)

    # Ensure bid is at least 1.0 to avoid bidding 0
    return max(1.0, final_bid)
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
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    # --- Bidding Strategy ---

    # Critical HP or missed water yesterday: Bid aggressively
    if my_status['hp'] <= 3 or my_status['no_water_days'] > 0:
        bid = DAILY_SALARY * 0.95 # High bid to ensure water
        if max_yesterday_bid > 0:
            bid = max(bid, max_yesterday_bid * 1.05) # Outbid previous high if necessary
        return min(my_status['budget'], bid)

    # End of the episode: Increase urgency
    if day_context['day'] >= EPISODE_DAYS - 2: # Last two days
        bid = DAILY_SALARY * 0.8
        if max_yesterday_bid > 0:
            bid = max(bid, max_yesterday_bid * 1.03) # Slightly outbid
        return min(my_status['budget'], bid)

    # Normal state bidding
    base_bid = DAILY_SALARY * 0.55

    # Adjust based on supply: lower supply means higher competition
    if day_context['supply'] <= 18: # Low supply
        base_bid *= 1.15
    elif day_context['supply'] >= 22: # High supply
        base_bid *= 0.9

    # Adjust based on yesterday's highest bid
    if max_yesterday_bid > 0:
        if max_yesterday_bid > DAILY_SALARY * 0.7: # If opponents bid high yesterday
            base_bid = max(base_bid, max_yesterday_bid * 1.01) # Try to slightly outbid
        elif max_yesterday_bid < DAILY_SALARY * 0.4: # If opponents bid low yesterday
            base_bid = min(base_bid, max_yesterday_bid * 1.1) # Don't overpay too much

    # Consider number of alive opponents: more opponents, more competition
    if num_alive_opponents >= 3:
        base_bid *= 1.05
    elif num_alive_opponents == 1:
        base_bid *= 0.95

    # Ensure a minimum bid to stay competitive
    final_bid = max(DAILY_SALARY * 0.2, base_bid)

    return min(my_status['budget'], final_bid)
"""
