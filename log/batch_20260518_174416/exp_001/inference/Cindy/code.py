# ============================================================
# Experiment: exp_001
# Agent: Cindy
# Source: exp_001
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_supply = day_context['supply']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Scenario 1: No opponents
    if num_alive_opponents == 0:
        # If my HP is full or enough for remaining days, no need for water, bid 0 to save budget.
        if my_hp >= (EPISODE_DAYS - current_day + 1):
            return 0
        # Otherwise, bid a very small amount to secure water.
        return min(my_budget, DAILY_SALARY * 0.1)

    # Scenario 2: Opponents exist
    yesterday_bids = []
    for opp_data in alive_opponents:
        prev = opp_data.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    bid_amount = DAILY_SALARY * 0.5 # Start with a moderate bid

    # Adjust bid based on my HP (survival priority)
    if my_hp <= 2: # Critical HP, must get water
        bid_amount = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP, need water soon
        bid_amount = DAILY_SALARY * 0.8
    elif my_hp >= (EPISODE_DAYS - current_day + 1): # Good HP, can afford to be conservative
        bid_amount = DAILY_SALARY * 0.3

    # Adjust bid based on opponent's previous behavior and current supply
    if max_yesterday_bid > 0:
        # If opponents bid high yesterday, increase my bid to compete
        if my_hp <= 4: # Desperate
            bid_amount = max(bid_amount, max_yesterday_bid + 5)
        else: # Not desperate, but competitive
            bid_amount = max(bid_amount, max_yesterday_bid * 1.05)
            # If supply is very good, don't overbid too much
            if current_supply >= WATER_REQ * 2:
                bid_amount = min(bid_amount, max(max_yesterday_bid, DAILY_SALARY * 0.4))
    else:
        # No high bids from opponents yesterday, implies they might be conservative or not desperate
        if my_hp <= 2: # Still desperate, bid high to be safe
            bid_amount = DAILY_SALARY * 0.9
        elif current_supply < WATER_REQ * 1.5 and num_alive_opponents > 0: # Tight supply, need to be competitive
            bid_amount = DAILY_SALARY * 0.6
        else: # Ample supply or no strong signals, try to save
            bid_amount = DAILY_SALARY * 0.35

    # Ensure bid does not exceed budget and is non-negative
    final_bid = min(my_budget, max(0, bid_amount))

    return int(final_bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimally to survive and save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Determine base bid based on my health and no-water days
    bid_amount = 0.0
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        # Desperate: Bid very aggressively
        if highest_prev_bid >= DAILY_SALARY * 0.8: # If opponents bid very high (>= 120)
            bid_amount = highest_prev_bid + 5.0
        else:
            bid_amount = DAILY_SALARY * 0.9 # Base 135
    elif my_status['hp'] <= 4:
        # Getting low: Bid moderately aggressively
        if highest_prev_bid >= DAILY_SALARY * 0.6: # If opponents bid high (>= 90)
            bid_amount = max(DAILY_SALARY * 0.7, highest_prev_bid + 2.0) # Base 105 or higher
        else:
            bid_amount = DAILY_SALARY * 0.7 # Base 105
    else:
        # Relatively healthy: Bid competitively
        if highest_prev_bid >= DAILY_SALARY * 0.5: # If opponents bid moderately (>= 75)
            bid_amount = max(DAILY_SALARY * 0.55, highest_prev_bid + 1.0) # Base 82.5 or higher
        else:
            bid_amount = DAILY_SALARY * 0.55 # Base 82.5

    # Further adjust bid based on supply scarcity
    supply = day_context['supply']
    if supply <= WATER_REQ: # Very low supply, only one full water requirement possible
        if my_status['hp'] <= 3 or my_status['no_water_days'] > 0:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.95) # 142.5
        else:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.8) # 120
    elif supply < 2 * WATER_REQ: # Moderate supply, enough for 1-2 agents to get water
        if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.9) # 135
        elif my_status['hp'] <= 4:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.75) # 112.5

    # Ensure bid does not exceed budget and has a strategic upper limit
    max_strategic_bid = DAILY_SALARY * 1.1 # Default cap at 110% of salary
    if my_status['hp'] <= 1 or my_status['no_water_days'] >= 2: # Extreme desperation
        max_strategic_bid = DAILY_SALARY * 1.2 # Willing to go up to 120% of salary

    final_bid = min(my_status['budget'], bid_amount, max_strategic_bid)

    # Ensure bid is not negative
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
    EPISODE_DAYS = 10
    MIN_SUPPLY = 15.0
    MAX_SUPPLY = 25.0

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_supply = day_context['supply']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid a minimal amount to secure water
    if not alive_opponents:
        # Ensure we always bid at least 1.0 to win water if no competition
        return min(my_budget, max(1.0, DAILY_SALARY * 0.1))

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Default bid if no previous bids or general case
    bid_amount = DAILY_SALARY * 0.75 # A solid base bid around 112.5

    # Adjust bid based on my HP
    if my_hp <= 1: # Critical HP, bid aggressively to survive
        bid_amount = DAILY_SALARY * 0.99
    elif my_hp <= 3: # Low HP, bid high
        bid_amount = DAILY_SALARY * 0.9
    elif my_status['no_water_days'] > 0: # Missed water yesterday, need to secure it today
        bid_amount = DAILY_SALARY * 0.85

    # Adjust bid based on opponent's previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents bid very high, react strongly
        if highest_prev_bid >= DAILY_SALARY * 0.85: # e.g., > 127.5
            if my_hp <= 3: # If I'm also in a tough spot, be very competitive
                bid_amount = max(bid_amount, highest_prev_bid + 5.0)
            else: # If my HP is good, but competition is high, still aim to win
                bid_amount = max(bid_amount, highest_prev_bid * 1.02)
        # If opponents bid moderately, stay competitive
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # e.g., > 90
            bid_amount = max(bid_amount, highest_prev_bid + 2.0)
        # If opponents bid low, try to win cheaply but don't risk losing water
        else: # highest_prev_bid < DAILY_SALARY * 0.6
            if my_hp > 3: # If I'm not desperate, try to save money
                bid_amount = min(bid_amount, highest_prev_bid + 10.0)
                bid_amount = max(bid_amount, DAILY_SALARY * 0.5) # Ensure a floor
            else: # Still need water, bid a bit higher than low bids
                bid_amount = max(bid_amount, highest_prev_bid + 5.0)

    # Adjust bid based on supply: lower supply means higher competition, so bid more
    # Normalize supply: 0 for max_supply, 1 for min_supply
    # Ensure division by non-zero for range
    supply_range_diff = MAX_SUPPLY - MIN_SUPPLY
    if supply_range_diff > 0:
        supply_norm = (MAX_SUPPLY - current_supply) / supply_range_diff
        # Add a small premium based on supply scarcity
        bid_amount += (DAILY_SALARY * 0.05) * supply_norm # Max 7.5 premium

    # Late game aggression if budget allows and HP is not critical
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 3:
        if my_budget >= DAILY_SALARY * 2 and my_hp > 2: # Good budget, not critical HP
            bid_amount = max(bid_amount, DAILY_SALARY * 0.85) # Be more aggressive
        elif my_hp <= 2: # Critical or low HP late game, bid very high
            bid_amount = DAILY_SALARY * 0.99
        elif my_budget < DAILY_SALARY and my_hp > 3: # Low budget late game, try to conserve if not desperate
            bid_amount = min(bid_amount, DAILY_SALARY * 0.6)

    # Ensure bid is at least 1.0 and does not exceed budget
    final_bid = max(1.0, bid_amount)
    final_bid = min(my_budget, final_bid)

    return float(final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Analyze yesterday's bids and identify David
    yesterday_bids = []
    david_alive = False
    david_yesterday_bid = 0

    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
            if opp_id == "David":
                david_alive = True
                if prev and prev.get('bid') is not None:
                    david_yesterday_bid = prev['bid']

    # --- Bidding Logic ---
    my_current_bid = 0

    # 1. Emergency Bid (Low HP)
    if my_status['hp'] <= 2:
        # Critical HP, bid very high to survive
        my_current_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        # Low HP, bid high
        my_current_bid = DAILY_SALARY * 0.8
    else:
        # 2. Normal Play - React to David or highest opponent bid
        base_target_bid = DAILY_SALARY * 0.5 # Default conservative bid

        if david_alive:
            # David is the primary competitor. Try to outbid him.
            if david_yesterday_bid > 0:
                # Try to beat his yesterday's bid by a small margin
                base_target_bid = min(DAILY_SALARY * 0.9, david_yesterday_bid + 5)
            else:
                # If no yesterday bid for David, assume he's strong
                base_target_bid = DAILY_SALARY * 0.85
        elif yesterday_bids:
            # David is not alive, but other opponents are. React to the highest bid.
            highest_prev_bid = max(yesterday_bids)
            if highest_prev_bid >= DAILY_SALARY * 0.7:
                base_target_bid = min(DAILY_SALARY * 0.8, highest_prev_bid + 2)
            else:
                base_target_bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)
        
        # 3. Adjust for late game (more aggressive if budget allows)
        days_left = EPISODE_DAYS - day_context['day'] + 1
        if days_left <= 3 and my_status['budget'] > DAILY_SALARY * 2: # If enough budget for a few more days
            base_target_bid = max(base_target_bid, DAILY_SALARY * 0.9)
        
        my_current_bid = base_target_bid

    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], my_current_bid)

    # Ensure a minimum bid to stay in contention
    min_bid_floor = DAILY_SALARY * 0.1
    return max(min_bid_floor, final_bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    EPISODE_DAYS = 10

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid strategy: Start with a moderate bid
    bid = DAILY_SALARY * 0.55

    # Adjust bid based on my HP (survival priority)
    if my_hp <= 2: # Critical HP
        bid = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP
        bid = DAILY_SALARY * 0.8
    elif my_hp <= 6: # Moderate HP
        bid = DAILY_SALARY * 0.7
    # Else, bid remains base_bid for high HP

    # Adjust bid based on supply scarcity
    # If supply is low, competition is higher, so bid more
    if (MAX_SUPPLY - MIN_SUPPLY) > 0: # Avoid division by zero
        # supply_factor ranges from 0 (max supply) to 1 (min supply)
        supply_factor = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
        bid += supply_factor * (DAILY_SALARY * 0.2) # Add up to 20% of salary based on scarcity

    # React to opponent's previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        max_opp_bid = max(yesterday_bids)
        # If max opponent bid was significantly higher than my current planned bid,
        # or if I need to secure water, try to outbid them.
        if max_opp_bid >= bid * 0.9: # If their max bid was close to or higher than my bid
            bid = max(bid, max_opp_bid + 5) # Try to slightly outbid them
        elif max_opp_bid < DAILY_SALARY * 0.4 and my_hp > 5: # If opponents bid very low and I'm healthy
            bid = min(bid, DAILY_SALARY * 0.45) # Conserve budget, but don't bid too low to lose water

    # Adjust bid for late game urgency or conservation
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last 2 days
        if my_hp > 5: # If healthy, try to conserve budget
            bid = min(bid, DAILY_SALARY * 0.6)
        else: # Critical days, must survive
            bid = max(bid, DAILY_SALARY * 0.9)
    elif remaining_days <= 4: # Mid-late game
        if my_hp <= 4: # If HP is getting low, be more aggressive
            bid = max(bid, DAILY_SALARY * 0.75)

    # Ensure bid does not exceed budget and is not negative
    bid = min(bid, my_budget)
    bid = max(bid, 0.0) # Bid can't be negative

    # Ensure a minimum bid to stay in the game, if budget allows
    if bid < DAILY_SALARY * 0.1 and my_budget >= DAILY_SALARY * 0.1:
        bid = DAILY_SALARY * 0.1

    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    if my_hp <= 2:
        return min(my_budget, DAILY_SALARY * 0.99)
    elif my_hp <= 4:
        return min(my_budget, DAILY_SALARY * 0.9)
    
    highest_prev_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])

    if highest_prev_bid == 0.0:
        if current_day <= EPISODE_DAYS / 2 and my_hp > EPISODE_DAYS / 2:
            base_bid = DAILY_SALARY * 0.55
        else:
            base_bid = DAILY_SALARY * 0.7
        return min(my_budget, base_bid)

    target_bid = highest_prev_bid + 2.5

    if my_hp > 4:
        target_bid = min(target_bid, DAILY_SALARY * 0.85)

    final_bid = min(my_budget, target_bid)
    
    return max(1.0, final_bid)
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
    MAX_HP = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid based on yesterday's highest competition
    base_bid = DAILY_SALARY * 0.6 # Moderate base (90)
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest bid was low, we can be slightly above it, but not too aggressive
        if highest_prev_bid < DAILY_SALARY * 0.7: # e.g., < 105
            base_bid = max(base_bid, highest_prev_bid + 5) # Bid slightly above
        else: # If highest bid was high, match or exceed it more aggressively
            base_bid = max(base_bid, highest_prev_bid + 10) # Bid more aggressively above
    else: # Day 1 or no previous bids
        base_bid = DAILY_SALARY * 0.7 # Start with a solid bid (105)

    current_bid = base_bid

    # Factor in HP urgency (always increases bid if critical)
    if my_status['hp'] <= 2: # Critical HP
        current_bid = max(current_bid, DAILY_SALARY * 0.98) # 147
    elif my_status['hp'] <= 5: # Low HP
        current_bid = max(current_bid, DAILY_SALARY * 0.88) # 132

    # Factor in supply scarcity (always increases bid if scarce)
    if day_context['supply'] == MIN_SUPPLY: # 15 units, extremely scarce
        current_bid = max(current_bid, DAILY_SALARY * 0.95) # 142.5
    elif day_context['supply'] <= WATER_REQ + 5: # 16-18 units, very scarce
        current_bid = max(current_bid, DAILY_SALARY * 0.85) # 127.5

    # Factor in number of opponents (always increases bid if many)
    if num_alive_opponents >= 3:
        current_bid = max(current_bid, DAILY_SALARY * 0.78) # 117
    elif num_alive_opponents == 2:
        current_bid = max(current_bid, DAILY_SALARY * 0.68) # 102

    # Final adjustment for healthy HP and abundant supply (to save budget)
    # This should potentially *reduce* the bid if it's too high and conditions allow
    if my_status['hp'] > 5 and day_context['supply'] == MAX_SUPPLY and num_alive_opponents < 3:
        # If healthy, abundant supply, and fewer opponents, we can afford to be less aggressive.
        # Cap the bid at a lower percentage of salary.
        current_bid = min(current_bid, DAILY_SALARY * 0.7) # 105
    elif my_status['hp'] > 5 and day_context['supply'] == MAX_SUPPLY:
        # If healthy and abundant supply, but still many opponents
        current_bid = min(current_bid, DAILY_SALARY * 0.75) # 112.5

    # Ensure bid doesn't exceed budget or daily salary cap
    final_bid = min(my_status['budget'], current_bid, DAILY_SALARY * 0.99) # Cap at almost full salary

    # Ensure bid is at least a minimal amount if I have budget and need water (not full HP)
    if final_bid <= 0 and my_status['budget'] > 0 and my_status['hp'] < MAX_HP:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

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

    # If no opponents, bid a small amount to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid strategy
    bid = DAILY_SALARY * 0.55 # Default moderate bid

    # 1. Prioritize survival if HP is low
    if my_status['hp'] <= 3: # Critical HP, prioritize water heavily
        bid = DAILY_SALARY * 0.95
        if highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid + 5) # Outbid if possible
    elif my_status['hp'] <= 6: # Mid-low HP, be more aggressive
        bid = DAILY_SALARY * 0.75
        if highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid + 3)
    else: # Healthy HP, react to opponents' previous bid
        if highest_prev_bid > DAILY_SALARY * 0.8: # Opponents very aggressive
            bid = highest_prev_bid + 2
        elif highest_prev_bid > DAILY_SALARY * 0.6: # Opponents moderately aggressive
            bid = highest_prev_bid + 1
        elif highest_prev_bid > 0 and highest_prev_bid < DAILY_SALARY * 0.5: # Opponents conservative
            bid = max(DAILY_SALARY * 0.4, highest_prev_bid + 1) # Still aim to win if cheap
        else: # No strong signal or very low bids, conservative default
            bid = DAILY_SALARY * 0.5

    # 2. Adjust for late game pressure
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 3 days
        bid = max(bid, DAILY_SALARY * 0.8) # Ensure high bid
        if highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid + 4) # Even more aggressive

    # 3. Adjust for supply scarcity
    # If supply is very low (e.g., only enough for one full requirement or slightly more)
    if day_context['supply'] <= WATER_REQ + 2: # Supply 13-15 units
        bid = max(bid, DAILY_SALARY * 0.85) # Increase aggression
        if highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid + 5)
    # If supply is ample (e.g., enough for more than one requirement)
    elif day_context['supply'] >= WATER_REQ * 1.8: # Supply 24-25 units
        # If my bid is already high and not critical HP, try to reduce it to save money
        if bid > DAILY_SALARY * 0.6 and my_status['hp'] > 3:
            bid = min(bid, DAILY_SALARY * 0.65)
        if highest_prev_bid > 0 and highest_prev_bid < DAILY_SALARY * 0.5: # Win cheaply if possible
            bid = min(bid, highest_prev_bid + 1)

    # Final check: Ensure bid is within budget and non-negative
    return max(0.0, min(my_status['budget'], bid))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return max(1.0, min(my_status['budget'], DAILY_SALARY * 0.3))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Decision logic based on yesterday's highest pressure and my HP
    if highest_prev_bid >= DAILY_SALARY * 0.8: # If opponents were bidding very high (>= 120)
        if my_status['hp'] > 4: # If I have decent HP (more than 4)
            # Try to save, but remain competitive. Bid slightly below their high to test.
            bid_amount = max(DAILY_SALARY * 0.6, highest_prev_bid * 0.9)
        else: # My HP is low (4 or less), need to secure water
            bid_amount = DAILY_SALARY * 0.9
    else: # Opponents were bidding moderately or lower (< 120)
        # Be competitive, slightly above their previous high, but not overspending
        bid_amount = max(DAILY_SALARY * 0.55, highest_prev_bid + 2.0)

    # Override for critical HP, ensuring survival
    if my_status['hp'] <= 2:
        bid_amount = DAILY_SALARY * 0.95

    # Ensure bid doesn't exceed budget and is at least 1.0
    return max(1.0, min(my_status['budget'], bid_amount))
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
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimal to save budget and secure water
    if not alive_opponents:
        return min(my_budget, 0.1)

    opponent_bids_yesterday = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            opponent_bids_yesterday.append(prev['bid'])

    # Base bid strategy
    # If no previous bids, start with a moderate bid
    if not opponent_bids_yesterday:
        target_bid = DAILY_SALARY * 0.65
    else:
        max_opp_bid = max(opponent_bids_yesterday)
        # Aim to slightly outbid the highest previous bid
        target_bid = max_opp_bid + 1.0 # Add 1.0 to ensure it's slightly higher and float for consistency

        # Ensure a minimum competitive bid even if opponents bid very low
        target_bid = max(target_bid, DAILY_SALARY * 0.5)

    # HP-based adjustments: Prioritize survival if HP is low
    if my_hp <= 2: # Critical HP
        target_bid = max(target_bid, DAILY_SALARY * 0.95)
    elif my_hp <= 5: # Low HP
        target_bid = max(target_bid, DAILY_SALARY * 0.8)
    else: # Healthy HP
        # For healthy HP, ensure it's at least a moderate bid, potentially slightly above average opponent bid
        if opponent_bids_yesterday:
            avg_opp_bid = sum(opponent_bids_yesterday) / len(opponent_bids_yesterday)
            target_bid = max(target_bid, avg_opp_bid * 1.05)
        target_bid = max(target_bid, DAILY_SALARY * 0.6)

    # Late game pressure adjustment: Be more aggressive towards the end of the episode
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        target_bid = max(target_bid, DAILY_SALARY * 0.9) # Ensure aggressive bidding to survive

    # Final safety checks:
    # 1. Bid must be positive
    # 2. Bid cannot exceed current budget
    final_bid = max(0.1, target_bid)
    final_bid = min(my_budget, final_bid)

    return final_bid
"""
