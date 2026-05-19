# ============================================================
# Experiment: exp_002
# Agent: Cindy
# Source: exp_002
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQ = 13
    MY_DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    # Identify alive opponents and their requirements
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_agents = len(alive_opponents) + 1 # Including myself

    total_water_needed_by_all = MY_WATER_REQ + sum(o['water_requirement'] for o in alive_opponents)

    # Base bid: a fraction of daily salary, aiming to save money but win
    base_bid = MY_DAILY_SALARY * 0.45

    # --- Emergency Bidding (Survival) ---
    # If HP is critically low (e.g., 2 or less) or I missed water yesterday
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        # Bid aggressively to ensure water, up to my budget
        return min(my_status['budget'], MY_DAILY_SALARY * 0.95)

    # --- Adjust bid based on supply scarcity ---
    # If supply is less than total water needed by all, competition will be high
    if day_context['supply'] < total_water_needed_by_all:
        base_bid = max(base_bid, MY_DAILY_SALARY * 0.6) # Increase bid for scarcity
        # If supply is barely enough for me, bid even higher
        if day_context['supply'] < MY_WATER_REQ:
            base_bid = max(base_bid, MY_DAILY_SALARY * 0.8)

    # --- Adjust bid based on opponent's previous behavior ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)
        max_yesterday_bid = max(yesterday_bids)

        # If opponents bid high yesterday, increase my bid to stay competitive
        if max_yesterday_bid >= MY_DAILY_SALARY * 0.7:
            base_bid = max(base_bid, max_yesterday_bid + 1.0) # Bid slightly above highest
        elif avg_yesterday_bid >= MY_DAILY_SALARY * 0.4:
            base_bid = max(base_bid, avg_yesterday_bid + 0.5) # Bid slightly above average

    # --- Adjust bid based on game day (later days might be more desperate) ---
    # day_context['day'] is 0-indexed for 10 days, so day 0 to 9
    if day_context['day'] >= EPISODE_DAYS - 3: # Last 3 days
        base_bid = max(base_bid, MY_DAILY_SALARY * 0.7) # Increase bid for end game pressure

    # Ensure bid is not negative and within budget
    final_bid = max(0.0, base_bid)
    final_bid = min(final_bid, my_status['budget'])

    # Ensure bid is at least 1 if I need water and can afford it
    if my_status['hp'] <= 9 and final_bid == 0 and my_status['budget'] > 0:
        return min(my_status['budget'], 1.0)

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

    alive_opponents = [o for o_id, o in opponents_status.items() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimum to get water and save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], 1.0)

    # Desperate for water (low HP)
    # If HP is 1 or 2, I MUST get water. Bid very high.
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.98)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid calculation
    base_bid = DAILY_SALARY * 0.5 # Default starting point

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Aim to outbid the highest opponent, especially since it's winner-take-all for water
        if my_status['hp'] > 5: # Good HP (6-10)
            # Try to win by a small margin, but ensure it's above a certain threshold
            base_bid = max(highest_prev_bid + 2, DAILY_SALARY * 0.6)
            base_bid = min(base_bid, DAILY_SALARY * 0.85) # Cap to save budget
        elif my_status['hp'] > 2: # Moderate HP (3-5)
            # Be more aggressive to secure water
            base_bid = max(highest_prev_bid + 5, DAILY_SALARY * 0.7)
            base_bid = min(base_bid, DAILY_SALARY * 0.9) # Higher cap
    else:
        # Day 1 or no previous bids available for current alive opponents
        # Initial competitive bid based on number of opponents
        if num_alive_opponents >= 3:
            base_bid = DAILY_SALARY * 0.75 # More competition, higher bid
        elif num_alive_opponents == 2:
            base_bid = DAILY_SALARY * 0.65
        else: # 1 opponent
            base_bid = DAILY_SALARY * 0.55

    # Adjust bid for late game pressure
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 3 and my_status['hp'] > 0: # Last few days, need to survive
        # Be very aggressive if still in the game
        base_bid = max(base_bid, DAILY_SALARY * 0.9)

    # Final bid must not exceed budget and must be at least 1.0
    final_bid = min(my_status['budget'], base_bid)
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid conservatively to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid
    base_bid = DAILY_SALARY * 0.6 # Start with a reasonable bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If my HP is low, I need water desperately, bid very aggressively
        if my_status['hp'] <= 3:
            # Bid slightly above the highest previous bid, or a high percentage of salary
            return min(my_status['budget'], max(highest_prev_bid + 2.0, DAILY_SALARY * 0.9))
        
        # If highest previous bid was very high (e.g., from Alex/David)
        if highest_prev_bid >= DAILY_SALARY * 0.85: # 150 * 0.85 = 127.5
            # If my HP is good, I can afford to be slightly less aggressive, but still competitive
            if my_status['hp'] > 5:
                return min(my_status['budget'], max(DAILY_SALARY * 0.75, highest_prev_bid + 1.0))
            else: # HP is somewhat low, need to be more aggressive
                return min(my_status['budget'], max(DAILY_SALARY * 0.85, highest_prev_bid + 1.5))
        
        # If highest previous bid was moderate
        else:
            # Bid slightly above it to secure water, but not excessively high
            return min(my_status['budget'], max(base_bid, highest_prev_bid + 1.5))
    
    # If no previous bids from alive opponents (e.g., first day or all died)
    # Or if the above conditions didn't trigger, use a default strategy
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    elif my_status['hp'] <= 5:
        return min(my_status['budget'], DAILY_SALARY * 0.7)
    else:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
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

    # If no opponents are alive, bid a minimal amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # Base bid: moderate proportion of daily salary
    bid_value = DAILY_SALARY * 0.6

    # Adjust bid based on my current HP
    if my_status['hp'] <= 2: # Critical HP, bid aggressively
        bid_value = DAILY_SALARY * 0.95
    elif my_status['hp'] == 1: # Extremely critical
        bid_value = DAILY_SALARY * 1.05 # Bid above salary if budget allows
    elif my_status['hp'] > 5: # Healthy, can afford to be less aggressive
        bid_value = DAILY_SALARY * 0.5

    # Adjust bid based on supply scarcity and opponent's previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        num_competitors = len(alive_opponents) + 1 # Myself + alive opponents

        # If supply is low relative to competitors, increase bid
        if day_context['supply'] < num_competitors * WATER_REQ * 0.8: # High scarcity
            bid_value = max(bid_value, highest_prev_bid + 10) # Be more aggressive
        elif day_context['supply'] < num_competitors * WATER_REQ: # Moderate scarcity
            bid_value = max(bid_value, highest_prev_bid + 5) # Slightly outbid

        # If highest opponent bid was very high, be competitive
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            bid_value = max(bid_value, highest_prev_bid + 5)
        # If highest opponent bid was low, try to win cheaply if healthy
        elif highest_prev_bid < DAILY_SALARY * 0.4 and my_status['hp'] > 3:
            bid_value = min(bid_value, highest_prev_bid + 2)

    # Adjust bid for end-game pressure
    current_day = day_context['day']
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        if my_status['hp'] <= 3: # Need to survive
            bid_value = max(bid_value, DAILY_SALARY * 1.05) # Maximize survival chance
        else: # Healthy but still want to finish strong
            bid_value = max(bid_value, DAILY_SALARY * 0.75)

    # Ensure the bid does not exceed current budget and is not negative
    final_bid = min(my_status['budget'], max(0.0, bid_value))

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    CRITICAL_HP = 3 # If HP is 3 or less, bid very aggressively
    LOW_HP = 6    # If HP is between 4 and 6, bid aggressively

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents are alive, bid minimum to get water and save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1) # Bid 15

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid based on HP
    bid = 0.0
    if my_status['hp'] <= CRITICAL_HP:
        # Critical HP, bid very aggressively to survive
        bid = DAILY_SALARY * 1.05 # e.g., 157.5
    elif my_status['hp'] <= LOW_HP:
        # Low HP, bid aggressively
        bid = DAILY_SALARY * 0.9 # e.g., 135
    else:
        # Healthy HP, bid moderately
        bid = DAILY_SALARY * 0.6 # e.g., 90

    # Adjust bid based on yesterday's highest opponent bid and supply
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        num_slots = int(day_context['supply'] // WATER_REQ)

        if num_slots == 1:
            # Only one water slot, competition is fierce
            if my_status['hp'] <= CRITICAL_HP:
                bid = max(bid, highest_prev_bid + 10) # Ensure outbid significantly
            elif my_status['hp'] <= LOW_HP:
                bid = max(bid, highest_prev_bid + 5)
            else:
                bid = max(bid, highest_prev_bid + 2) # Slightly above to win
        else: # num_slots >= 2
            # Two or more water slots, potentially less fierce
            if my_status['hp'] <= CRITICAL_HP:
                bid = max(bid, highest_prev_bid + 5)
            elif my_status['hp'] <= LOW_HP:
                bid = max(bid, highest_prev_bid + 2)
            else:
                # If healthy and multiple slots, try to get it cheaper but still competitive
                if highest_prev_bid < DAILY_SALARY * 0.5: 
                    bid = max(bid, DAILY_SALARY * 0.6)
                else:
                    bid = max(bid, highest_prev_bid * 0.95) # Try to get it slightly cheaper
    else: # No previous bids from currently alive opponents (e.g., all new or no bids yet)
        # If no previous bids, and supply is low, bid a bit higher proactively
        if int(day_context['supply']) <= WATER_REQ * 1.5: # e.g., supply 15-19, means 1 slot or tight 2 slots
            if my_status['hp'] <= CRITICAL_HP:
                bid = max(bid, DAILY_SALARY * 0.9) # 135
            elif my_status['hp'] <= LOW_HP:
                bid = max(bid, DAILY_SALARY * 0.75) # 112.5
            else:
                bid = max(bid, DAILY_SALARY * 0.65) # 97.5
        # else, bid remains as determined by HP

    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], bid)

    # Ensure bid is at least 1 (to participate and avoid errors)
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    bid = DAILY_SALARY * 0.5 

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: 
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] == 3:
        bid = DAILY_SALARY * 0.8
    elif my_status['hp'] == 4:
        bid = DAILY_SALARY * 0.7
    else: # Healthy HP
        # Adjust bid based on supply and competition
        num_possible_winners = int(day_context['supply'] // WATER_REQ)

        if num_possible_winners == 0: 
            bid = max(bid, DAILY_SALARY * 0.85)
        elif num_possible_winners <= num_alive_opponents: 
            bid = max(bid, DAILY_SALARY * 0.65)
        else: 
            bid = min(bid, DAILY_SALARY * 0.45)

        # Adjust bid based on highest previous bid
        if highest_prev_bid > 0:
            if highest_prev_bid >= DAILY_SALARY * 0.8: 
                if my_status['hp'] > 4: 
                    bid = max(bid, highest_prev_bid * 0.9)
                else: 
                    bid = max(bid, highest_prev_bid + 5)
            elif highest_prev_bid >= DAILY_SALARY * 0.5: 
                bid = max(bid, highest_prev_bid + 2)
            else: 
                bid = max(bid, highest_prev_bid + 1)

    # Endgame strategy
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: 
        if my_status['hp'] <= 5: 
            bid = max(bid, DAILY_SALARY * 0.9)
        else: 
            bid = max(bid, DAILY_SALARY * 0.7)

    bid = min(bid, my_status['budget'])
    bid = max(bid, 0.01)

    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid a low amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Decision logic based on yesterday's highest pressure and my health
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If opponents bid very high yesterday (e.g., >= 80% of my salary)
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 4: # Healthy, can afford to be slightly less aggressive but still competitive
                # Aim to win but avoid overpaying if possible, considering high previous bids
                bid = max(DAILY_SALARY * 0.7, highest_prev_bid * 0.95)
            else: # Low HP, need water desperately
                bid = highest_prev_bid + 5 # Try to outbid
        # If opponents bid moderately yesterday
        else:
            # Stay competitive, slightly above highest previous bid
            bid = max(DAILY_SALARY * 0.6, highest_prev_bid + 5)
    else:
        # No clear bidding history, rely on my health
        if my_status['hp'] <= 3: # Low HP, bid aggressively
            bid = DAILY_SALARY * 0.9
        else: # Moderate HP, bid robustly
            bid = DAILY_SALARY * 0.7

    # Ensure bid does not exceed budget and is at least a minimal amount
    final_bid = min(my_status['budget'], bid)
    final_bid = max(1.0, final_bid)

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

    # If it's the last day and I need water, bid almost everything
    if day_context['day'] == EPISODE_DAYS and my_status['hp'] > 0:
        return max(1.0, my_status['budget'] * 0.99)

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimum to get water
    if not alive_opponents:
        return max(1.0, min(my_status['budget'], DAILY_SALARY * 0.1))

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid strategy
    current_bid = DAILY_SALARY * 0.6 # Default moderate bid (90)

    # Aggressive bidding if HP is critically low
    if my_status['hp'] <= 3:
        current_bid = DAILY_SALARY * 0.98 # Very aggressive (147)
    # Less aggressive but still high if HP is moderately low
    elif my_status['hp'] <= 5:
        current_bid = DAILY_SALARY * 0.85 # High (127.5)

    # Adjust bid based on yesterday's opponent behavior
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.85: # Opponents were very aggressive
            if my_status['hp'] > 5: # I have some buffer, try to win but save a bit
                current_bid = max(current_bid, highest_prev_bid + 5) # Bid slightly above, but not excessively
                current_bid = min(current_bid, DAILY_SALARY * 0.9) # Cap it to avoid overspending too much
            else: # My HP is low, I need water, bid very high
                current_bid = DAILY_SALARY * 0.99
        else: # Opponents were moderate or low
            # Bid slightly above the highest previous bid to win by a small margin
            current_bid = max(current_bid, highest_prev_bid + 2.5)
            # Ensure the bid is not too low, even if opponents bid low
            current_bid = max(current_bid, DAILY_SALARY * 0.5)

    # Ensure bid does not exceed available budget and is at least 1.0
    final_bid = min(my_status['budget'], current_bid)
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    remaining_days = EPISODE_DAYS - day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_prev_bid = 0
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)

    # Critical state: HP is very low (can survive 1-2 more days) or missed water recently
    if my_status['hp'] <= WATER_REQ * 2 or my_status['no_water_days'] > 0:
        if remaining_days <= 1:
            # Last day, bid almost everything to survive
            return min(my_status['budget'], DAILY_SALARY * 0.99)
        else:
            # Aggressive bid to secure water
            return min(my_status['budget'], DAILY_SALARY * 0.85)

    # Strategic state: Opponents were bidding high yesterday
    if max_prev_bid > DAILY_SALARY * 0.7:
        # If I have enough budget to slightly outbid them
        if my_status['budget'] > max_prev_bid + 10:
            return min(my_status['budget'], max_prev_bid + 5)
        else:
            # Cannot afford to outbid high, try a moderate bid
            return min(my_status['budget'], DAILY_SALARY * 0.6)
    
    # Normal state: Moderate bidding
    return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimum to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid
    # A strong base bid is needed as only one player can fulfill their water requirement
    base_bid = DAILY_SALARY * 0.85 

    # Adjust bid based on my HP
    if my_status['hp'] <= 3: # Critical HP
        base_bid = DAILY_SALARY * 0.98 # Very aggressive to survive
    elif my_status['hp'] <= 5: # Low HP
        base_bid = DAILY_SALARY * 0.92
    else: # Healthy HP
        base_bid = DAILY_SALARY * 0.85

    # Adjust bid based on day (become more aggressive towards the end)
    if day_context['day'] >= EPISODE_DAYS - 2: # Last few days
        base_bid += 7.0 # Increase bid significantly
    elif day_context['day'] <= 2: # Early days, try to conserve a bit if healthy
        if my_status['hp'] > 5:
            base_bid -= 5.0 # Decrease bid slightly to conserve

    # React to highest opponent bid from yesterday if available
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest bid was very high, we need to be competitive
        if highest_prev_bid >= DAILY_SALARY * 0.9: # Opponent bid very high (e.g., >135)
            base_bid = max(base_bid, highest_prev_bid + 1.5) # Try to outbid by a small margin
        elif highest_prev_bid >= DAILY_SALARY * 0.8: # Opponent bid high (e.g., >120)
            base_bid = max(base_bid, highest_prev_bid + 0.5)
        else:
            # If previous bids were low, ensure a minimum competitive bid still
            base_bid = max(base_bid, DAILY_SALARY * 0.75)

    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure bid is a positive value
    final_bid = max(1.0, final_bid)

    return final_bid
"""
