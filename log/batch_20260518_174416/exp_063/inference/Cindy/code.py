# ============================================================
# Experiment: exp_063
# Agent: Cindy
# Source: exp_063
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

    # 1. Base bid: A moderate amount.
    bid = DAILY_SALARY * 0.5

    # 2. Adjust for no opponents: Bid minimally to save budget.
    if num_alive_opponents == 0:
        return min(my_status['budget'], 1)

    # 3. Adjust for my HP: If desperate (low HP), bid aggressively.
    if my_status['hp'] <= 2:
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] == 3: # Getting low, increase bid
        bid = DAILY_SALARY * 0.8
    else: # Comfortable HP, react to opponents and supply
        # 4. Adjust based on yesterday's opponent bids
        yesterday_bids = []
        for opp in alive_opponents:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

            # If opponents were very aggressive yesterday, bid slightly higher to win.
            if highest_prev_bid >= DAILY_SALARY * 0.8:
                bid = max(bid, highest_prev_bid + 5) 
            # If opponents were moderately aggressive.
            elif highest_prev_bid >= DAILY_SALARY * 0.6:
                bid = max(bid, avg_prev_bid + 2)
            # If opponents were conservative, try to win cheaply.
            else:
                bid = min(bid, avg_prev_bid + 1)

        # 5. Adjust based on supply scarcity
        # Calculate how many full water requirements can be met by current supply.
        num_slots = int(day_context['supply'] / WATER_REQ)

        # If supply is very tight (not enough for everyone including me), increase bid.
        if num_slots <= num_alive_opponents: 
            bid = max(bid, DAILY_SALARY * 0.75) 
        # If supply is abundant (more slots than competitors + me), try to get it cheaper.
        elif num_slots > num_alive_opponents + 1: 
            bid = min(bid, DAILY_SALARY * 0.4)

    # Final check: Ensure bid is within budget and positive.
    final_bid = max(1, min(my_status['budget'], bid))

    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From current meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimum to get water
    if not alive_opponents:
        return min(my_status['budget'], 1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid calculation
    # Default to a strong bid if no previous bids or if it's early
    base_bid = DAILY_SALARY * 0.75 # A good starting point

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If the highest previous bid was significant, aim to outbid it
        if highest_prev_bid > DAILY_SALARY * 0.5:
            base_bid = highest_prev_bid + (DAILY_SALARY * 0.05) # Bid slightly higher
        else: # Opponents might be passive, but don't get complacent
            base_bid = max(base_bid, DAILY_SALARY * 0.6) # Ensure a minimum competitive bid

    # Aggressive bidding if HP is low
    if my_status['hp'] <= 5: # Critical HP, must get water
        base_bid = max(base_bid, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 10: # Low HP, be more aggressive
        base_bid = max(base_bid, DAILY_SALARY * 0.85)

    # Increase bid aggressiveness towards the end of the episode
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 3: # Last few days, push harder
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    
    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure bid is at least 1 (to participate)
    return max(1, final_bid)
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

    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # If HP is critical, bid high to survive
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # If near end of episode, bid higher to ensure survival
    if day_context['day'] >= EPISODE_DAYS - 2:
        return min(my_status['budget'], DAILY_SALARY * 0.85)

    # General strategy based on yesterday's highest bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents are bidding very high
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            # If my HP is good, try to bid slightly less to save money but remain competitive
            if my_status['hp'] > 4:
                return min(my_status['budget'], max(DAILY_SALARY * 0.6, highest_prev_bid * 0.9))
            # If my HP is not great, I need to match/exceed
            return min(my_status['budget'], highest_prev_bid + 5.0)

        # If opponents are bidding moderately or low
        return min(my_status['budget'], max(DAILY_SALARY * 0.55, highest_prev_bid + 2.5))

    # Default bid if no previous bids (e.g., Day 1 or all opponents are new/no trace)
    return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no active opponents, bid low to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Default bid if no strong signals or for initial rounds
    default_bid = DAILY_SALARY * 0.55

    # Adjust bid based on my HP
    if my_status['hp'] <= 2:
        # Critical HP, bid very aggressively to survive
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4:
        # Low HP, bid aggressively
        default_bid = DAILY_SALARY * 0.8
    
    # Adjust bid further based on opponents' previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            # Opponents are bidding very high, need to compete strongly
            if my_status['hp'] > 4:
                # Healthy HP, try to win by slightly exceeding, but don't overspend if not critical
                return min(my_status['budget'], max(default_bid, highest_prev_bid + 5))
            else:
                # My HP is already low (3 or 4), must win this round
                return min(my_status['budget'], highest_prev_bid + 10)
        
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            # Opponents are bidding moderately, try to win by slightly exceeding
            return min(my_status['budget'], max(default_bid, highest_prev_bid + 2))
        
        else:
            # Opponents are bidding low, maintain a moderate bid or slightly above them
            return min(my_status['budget'], max(default_bid, highest_prev_bid + 1))
            
    # If no previous bids from opponents, or no specific condition met, use the calculated default bid
    return min(my_status['budget'], default_bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    my_current_budget = my_status['budget']
    my_current_hp = my_status['hp']
    current_supply = day_context['supply']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_current_budget, DAILY_SALARY * 0.2)

    bid = DAILY_SALARY * 0.65 # Moderate base bid

    eric_status = None
    alex_status = None
    for opp_id, opp in opponents_status.items():
        if opp_id == "Eric":
            eric_status = opp
        elif opp_id == "Alex":
            alex_status = opp

    eric_prev_bid = 0
    eric_budget = 0
    if eric_status and eric_status['alive']:
        prev = eric_status.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            eric_prev_bid = prev['bid']
        eric_budget = eric_status['budget']

    alex_prev_bid = 0
    alex_budget = 0
    if alex_status and alex_status['alive']:
        prev = alex_status.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            alex_prev_bid = prev['bid']
        alex_budget = alex_status['budget']

    # Adjust bid based on my HP
    if my_current_hp <= 2:
        bid = DAILY_SALARY * 0.95
    elif my_current_hp <= 4:
        bid = DAILY_SALARY * 0.85

    # Adjust bid based on supply scarcity
    if current_supply <= WATER_REQ + 2:
        bid *= 1.15
    elif current_supply <= WATER_REQ + 5:
        bid *= 1.05

    # Counter Eric's aggressive bidding if he has budget
    if eric_prev_bid > 0 and eric_budget >= DAILY_SALARY * 1.5:
        if eric_prev_bid > DAILY_SALARY * 0.7:
            bid = max(bid, eric_prev_bid * 1.05)
        else:
            bid = max(bid, eric_prev_bid * 1.01)
    elif eric_prev_bid > 0: # Eric bid high but might not have huge budget
        bid = max(bid, eric_prev_bid * 1.01)

    # Counter Alex, but less aggressively due to his low budget
    if alex_prev_bid > 0 and alex_budget > 0 and alex_budget < DAILY_SALARY:
        if alex_prev_bid > DAILY_SALARY * 0.7 and current_supply <= WATER_REQ + 5:
            bid = max(bid, alex_prev_bid * 1.02)
        else:
            bid = max(bid, alex_prev_bid * 0.95)

    # Late game desperation
    if current_day > EPISODE_DAYS * 0.7:
        if my_current_hp <= 5:
            bid = DAILY_SALARY * 0.99
        elif my_current_hp > 8:
            bid *= 0.9

    final_bid = min(my_current_budget, bid)

    if final_bid < DAILY_SALARY * 0.1 and my_current_budget > 0:
        final_bid = min(my_current_budget, DAILY_SALARY * 0.1)
    elif my_current_budget == 0:
        final_bid = 0

    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state
    MIN_SUPPLY = 15 # From meta-round state
    MAX_SUPPLY = 25 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimal to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1) # Bid 10% of salary

    yesterday_bids = []
    # Collect yesterday's bids from alive opponents
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine highest previous bid, default to a low value if no bids found
    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid strategy
    # Calculate a base bid based on my daily salary
    base_bid = DAILY_SALARY * 0.7 # Start with 70% of salary

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP
        base_bid = DAILY_SALARY * 1.1 # Bid aggressively to survive
    elif my_status['hp'] <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.9 # Bid high
    else: # Stable HP
        base_bid = DAILY_SALARY * 0.6 # Can be more conservative

    # Adjust bid based on opponent pressure (highest previous bid)
    # If opponents bid high, I need to consider bidding higher
    if highest_prev_bid > base_bid * 0.8: # If opponent's bid was significantly high
        # Try to outbid by a small margin, or match if my base bid is already high
        base_bid = max(base_bid, highest_prev_bid + (DAILY_SALARY * 0.05)) # Bid slightly above

    # Adjust bid based on day progress (late game pressure)
    # As the game progresses, water becomes more critical, so increase bid
    day_factor = day_context['day'] / EPISODE_DAYS
    base_bid *= (1 + day_factor * 0.15) # Up to 15% increase by last day

    # Adjust bid based on supply (less supply -> higher competition -> higher bid)
    supply_range_size = MAX_SUPPLY - MIN_SUPPLY
    if supply_range_size == 0:
        supply_ratio = 0.5 # Default to middle if range is 0
    else:
        supply_ratio = (day_context['supply'] - MIN_SUPPLY) / supply_range_size

    # If supply is low (supply_ratio close to 0), increase bid. If high (supply_ratio close to 1), decrease bid.
    supply_adjustment_factor = 1 + (1 - supply_ratio) * 0.2
    base_bid *= supply_adjustment_factor

    # Final bid must be clamped by budget and non-negative
    final_bid = min(my_status['budget'], base_bid)
    final_bid = max(final_bid, 0.0) # Ensure bid is not negative

    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    supply = day_context['supply']
    day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to secure water
    if num_alive_opponents == 0:
        # If there's supply, bid 1.0 to get it, otherwise 0
        return min(my_budget, 1.0) if supply > 0 else 0.0

    # Identify opponents with high daily salary and water requirement, similar to Cindy (or Alex/Bob)
    # These are the primary competitors for water.
    strong_competitor_bids_yesterday = []
    for opp in alive_opponents:
        # Assuming "strong" means similar economic profile to me (Cindy) or Alex/Bob
        if opp['daily_salary'] >= DAILY_SALARY * 0.9 and opp['water_requirement'] >= WATER_REQ * 0.9:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                strong_competitor_bids_yesterday.append(prev['bid'])

    # Base bid calculation
    base_bid = DAILY_SALARY * 0.55 # Default moderate bid

    # 1. Adjust bid based on my HP
    if my_hp <= 2: # Critical HP, must get water
        base_bid = DAILY_SALARY * 0.98 # Bid very aggressively
    elif my_hp <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.85
    elif my_hp > 7 and my_budget > DAILY_SALARY * 5: # High HP and good budget, can be more conservative
        base_bid = DAILY_SALARY * 0.45

    # 2. Adjust bid based on strong competitor's previous bids (yesterday's highest)
    if strong_competitor_bids_yesterday:
        max_prev_strong_bid = max(strong_competitor_bids_yesterday)
        if max_prev_strong_bid >= DAILY_SALARY * 0.8: # Strong opponents are bidding very high
            if my_hp <= 4: # If my HP is low, I must outbid
                base_bid = max(base_bid, max_prev_strong_bid + 5)
            else: # If HP is good, I can be slightly less aggressive but still competitive
                base_bid = max(base_bid, max_prev_strong_bid + 1)
        elif max_prev_strong_bid >= DAILY_SALARY * 0.5: # Strong opponents are bidding moderately
            base_bid = max(base_bid, max_prev_strong_bid + 2) # Slightly increase to secure

    # 3. Adjust for supply scarcity relative to demand
    # Calculate total water potentially needed if everyone gets their requirement
    total_water_demand = (num_alive_opponents + 1) * WATER_REQ
    if supply < total_water_demand:
        # Water is scarce. Increase bid.
        # How many full water_reqs can be satisfied?
        num_full_reqs_possible = int(supply // WATER_REQ) # CRITICAL: int() for division result
        if num_full_reqs_possible < (num_alive_opponents + 1): # Not enough for everyone
            # If I am near the bottom of HP, I must bid very high
            if my_hp <= 3:
                base_bid = max(base_bid, DAILY_SALARY * 0.95)
            # If it's very scarce (e.g., supply < WATER_REQ * 1.5 for multiple players)
            elif supply < WATER_REQ * 1.5 and num_alive_opponents >= 1:
                base_bid = max(base_bid, DAILY_SALARY * 0.9)
            else:
                base_bid = max(base_bid, DAILY_SALARY * 0.75)


    # 4. Adjust for day progression (end game aggression)
    if day >= 8: # Last few days
        if my_hp <= 5:
            base_bid = max(base_bid, DAILY_SALARY * 0.98)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.85)
    elif day >= 5: # Mid-game
        base_bid = max(base_bid, DAILY_SALARY * 0.7)

    # Final bid must not exceed budget and must be non-negative
    final_bid = min(my_budget, base_bid)
    final_bid = max(0.0, final_bid) # Ensure bid is not negative

    # If there's supply but my bid is 0 (due to budget or other logic), bid a minimum to try and get it
    if supply > 0 and final_bid < 1.0 and my_budget > 0:
        final_bid = min(my_budget, 1.0)
    elif supply == 0: # No supply, no point in bidding
        final_bid = 0.0

    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQUIREMENT = 13
    MY_DAILY_SALARY = 150
    TOTAL_DAYS = 10

    days_left = TOTAL_DAYS - day_context['day'] + 1

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], MY_DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Opponents show max bids around 151-152. Aim to beat this when critical.
    bid_to_win = MY_DAILY_SALARY * 1.05 + 5.0 # Aims for ~162.5

    current_bid = 0.0

    if my_status['hp'] <= 2: # Critical HP: Must win
        current_bid = bid_to_win
        if days_left == 1: # Go all in on the last day if critical
            current_bid = my_status['budget']
    elif my_status['hp'] <= 4: # Low HP: Need water soon
        current_bid = max(highest_prev_bid + 2.0, MY_DAILY_SALARY * 0.95) # Ensure competitive floor
    elif my_status['hp'] <= 7: # Moderate HP: Be competitive
        current_bid = max(highest_prev_bid + 1.0, MY_DAILY_SALARY * 0.8) # Ensure competitive floor
    else: # High HP (8-10): Save budget
        current_bid = MY_DAILY_SALARY * 0.6
        if highest_prev_bid < MY_DAILY_SALARY * 0.5: # If others are bidding very low
            current_bid = MY_DAILY_SALARY * 0.4

    current_bid = min(current_bid, my_status['budget'])

    if current_bid <= 0.01 and my_status['budget'] > 0: # Bid minimal if budget is low but not zero
        return 0.01
    elif current_bid <= 0.01 and my_status['budget'] <= 0: # Cannot bid if no budget
        return 0.0

    return current_bid
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

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    is_hp_critical = my_status['hp'] <= 2 or my_status['no_water_days'] > 0
    is_hp_low = my_status['hp'] <= 4

    bid_amount = 0

    if is_hp_critical:
        bid_amount = DAILY_SALARY * 1.1
    elif is_hp_low:
        if highest_prev_bid > DAILY_SALARY * 0.8:
            bid_amount = highest_prev_bid + 5
        else:
            bid_amount = DAILY_SALARY * 0.85
    else:
        if highest_prev_bid > DAILY_SALARY * 0.9:
            bid_amount = DAILY_SALARY * 0.5
        elif highest_prev_bid > DAILY_SALARY * 0.6:
            bid_amount = highest_prev_bid + 2.5
        else:
            bid_amount = DAILY_SALARY * 0.7

    return min(my_status['budget'], bid_amount)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_active_opponents = len(alive_opponents)

    # Base bid strategy
    base_bid = DAILY_SALARY * 0.65

    # --- Adjustments based on my status ---

    # Critical HP: Bid very aggressively to survive
    if my_hp <= 2:
        base_bid = DAILY_SALARY * 0.95
    # Low HP: Bid aggressively
    elif my_hp <= 4:
        base_bid = DAILY_SALARY * 0.85
    # Healthy HP but low budget: Conserve
    elif my_hp > 5 and my_budget < DAILY_SALARY * 2:
        base_bid = min(base_bid, DAILY_SALARY * 0.5)

    # --- Adjustments based on day and supply ---

    # Late game: Become more aggressive as days run out
    if current_day >= EPISODE_DAYS - 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    # Early game: Can be slightly less aggressive if not in danger
    elif current_day <= 2 and my_hp > 5:
        base_bid = min(base_bid, DAILY_SALARY * 0.6)

    # Supply scarcity: If supply is low relative to potential demand
    potential_total_demand = (num_active_opponents + 1) * WATER_REQ
    if current_supply < potential_total_demand * 0.7:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    elif current_supply > potential_total_demand * 1.2:
        base_bid = min(base_bid, DAILY_SALARY * 0.55)

    # --- Adjustments based on opponent's previous bids ---

    previous_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        # Only consider bids where water was successfully acquired ('SUCCESS' status)
        if prev and prev.get('bid') is not None and prev.get('status') == 'SUCCESS':
            previous_bids.append(prev['bid'])

    if previous_bids:
        max_prev_bid = max(previous_bids)
        avg_prev_bid = sum(previous_bids) / len(previous_bids)

        # If opponents were bidding high, react to stay competitive
        if max_prev_bid >= DAILY_SALARY * 0.8:
            if my_hp <= 4:
                base_bid = max(base_bid, max_prev_bid * 1.05) # Bid slightly above to ensure win
            else:
                base_bid = max(base_bid, max_prev_bid * 1.01) # Slightly higher than max
        elif avg_prev_bid >= DAILY_SALARY * 0.65:
            base_bid = max(base_bid, avg_prev_bid * 1.02) # Slightly higher than average

    # --- Final bid constraints ---

    # Ensure bid is at least a minimum value to participate
    final_bid = max(0.1, base_bid)

    # Ensure bid does not exceed my budget
    final_bid = min(final_bid, my_budget)

    # If I'm very low on HP and budget is also low, I might need to spend almost everything
    if my_hp <= 2 and my_budget > 0 and final_bid < my_budget * 0.8:
        final_bid = my_budget * 0.9 # Spend a large portion of remaining budget

    return round(final_bid, 2)
"""
