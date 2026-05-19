# ============================================================
# Experiment: exp_112
# Agent: Cindy
# Source: exp_112
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQ = 13
    MY_DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o_id, o in opponents_status.items() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Determine base bid based on my urgency
    base_bid = 0
    if my_status['no_water_days'] >= 1 or my_status['hp'] <= 2:
        # Critical state: Must get water
        base_bid = MY_DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        # Low HP: Need water soon
        base_bid = MY_DAILY_SALARY * 0.75
    else:
        # Healthy: Can be more conservative
        base_bid = MY_DAILY_SALARY * 0.5

    # Collect yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    final_bid = base_bid

    # Adjust bid based on opponent's previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= MY_DAILY_SALARY * 0.8: # Opponents were bidding high
            if my_status['no_water_days'] >= 1 or my_status['hp'] <= 4:
                # Urgent, match or slightly exceed high bids
                final_bid = max(final_bid, highest_prev_bid + 5)
            else:
                # Not urgent, but stay competitive
                final_bid = max(final_bid, highest_prev_bid + 2)
        else: # Opponents were bidding moderately or low
            final_bid = max(final_bid, highest_prev_bid + 1) # Bid slightly above to win
    
    # Adjust bid based on current supply and competition
    current_supply = day_context['supply']
    
    # Estimate total water needed if everyone gets their requirement
    total_water_needed_by_active = MY_WATER_REQ + sum(o['water_requirement'] for o in alive_opponents)

    if current_supply < total_water_needed_by_active:
        # Supply is tight, competition will be higher
        final_bid *= 1.1 # Increase bid
    elif current_supply >= total_water_needed_by_active + 5: # Generous supply, more than enough
        # Supply is abundant, can try to save money if not urgent
        if my_status['hp'] > 4:
            final_bid *= 0.9 # Decrease bid
    
    # Ensure bid is within budget and is at least 1
    final_bid = min(final_bid, my_status['budget'])
    final_bid = max(1, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta_round_state

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Calculate how many agents can theoretically get water
    num_possible_winners = int(current_supply // WATER_REQ)

    # Base bid, adjusted for my HP
    base_bid = DAILY_SALARY * 0.4 # Default conservative bid

    if my_hp <= 2: # Critical HP, must get water
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP, strong need for water
        base_bid = DAILY_SALARY * 0.75
    elif my_no_water_days > 0: # Missed water yesterday, need to secure it today
        base_bid = DAILY_SALARY * 0.6

    # If I'm the only one left, bid minimally to win
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Analyze previous day's bids from opponents
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev_trace = opp.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                yesterday_bids.append(prev_trace['bid'])

    # Adjust bid based on competition and supply
    if num_possible_winners == 0: # No one can get water, bid low to save budget
        return min(my_budget, DAILY_SALARY * 0.01)
    elif num_possible_winners >= num_alive_opponents + 1: # Plenty of water for everyone
        # Bid conservatively, just enough to ensure a win, if not desperate
        if my_hp > 4:
            base_bid = DAILY_SALARY * 0.25 # Lower bid if not desperate and supply is high
        else: # Still need to secure water even if supply is high
            base_bid = max(base_bid, DAILY_SALARY * 0.4)
    else: # Competition for water (num_possible_winners < num_alive_opponents + 1)
        if yesterday_bids:
            max_prev_bid = max(yesterday_bids)
            # If competition is high, bid above the max previous bid
            # The margin depends on my HP
            if my_hp <= 2: # Desperate
                base_bid = max(base_bid, max_prev_bid + 10) # Aggressive increase
            elif my_hp <= 4: # Low
                base_bid = max(base_bid, max_prev_bid + 5) # Moderate increase
            else: # Healthy
                base_bid = max(base_bid, max_prev_bid + 2) # Slight increase
        else:
            # If no previous bids are available (e.g., Day 1), use general competitive bid
            # informed by historical meta-round context (Alex/Eric are strong bidders).
            if my_hp <= 4:
                base_bid = max(base_bid, DAILY_SALARY * 0.8) # Higher if low HP
            else:
                base_bid = max(base_bid, DAILY_SALARY * 0.6) # Moderate if healthy

    # Consider the day in the episode. Towards the end, bids might get more desperate.
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last few days
        if my_hp <= 4: # Desperate to survive
            base_bid = max(base_bid, DAILY_SALARY * 0.99) # Bid almost full salary
        elif my_hp > 6 and my_budget > DAILY_SALARY * 5: # Healthy and rich, can afford to be more aggressive
            base_bid = max(base_bid, DAILY_SALARY * 0.7)

    # Ensure final bid does not exceed budget and is at least 1.0
    final_bid = min(my_budget, base_bid)
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From Current Meta-Round State

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)
    
    # If no opponents, bid minimally to save budget, but ensure water.
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.4) 

    current_day = day_context['day']
    current_supply = day_context['supply']

    # Base bid strategy
    # Start with a moderate bid, slightly above what might be considered cheap
    base_bid = DAILY_SALARY * 0.55 

    # Adjust bid based on my status (survival priority)
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        base_bid = DAILY_SALARY * 0.9 # Aggressive bid for survival
    if my_status['hp'] <= 1 or current_day >= EPISODE_DAYS - 2: # Critical HP or late game
        base_bid = DAILY_SALARY - 1.0 # Very aggressive, almost full salary

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Calculate available water units
    num_water_units = int(current_supply // WATER_REQ)
    num_total_bidders = num_alive_opponents + 1 # Including myself

    # Adjust bid based on opponent behavior and supply scarcity
    if num_water_units == 0:
        # No water available for anyone, bid 0 to save budget
        base_bid = 0.0
    elif num_water_units >= num_total_bidders:
        # Supply is abundant, competition is low. Try to get water cheaper.
        if highest_prev_bid > 0:
            # Bid slightly below previous max if possible, but not too low
            base_bid = min(base_bid, highest_prev_bid * 0.95)
        else:
            base_bid = min(base_bid, DAILY_SALARY * 0.4) # Low bid if no clear competition
    else:
        # Supply is scarce, competition is high. Bid higher.
        # Ensure we bid above previous max to increase chances
        base_bid = max(base_bid, highest_prev_bid + 2.0) 
        
        if num_water_units == 1: # Extreme scarcity, only one unit available
            base_bid = max(base_bid, DAILY_SALARY * 0.85, highest_prev_bid + 5.0)
        elif num_water_units <= num_total_bidders // 2: # High scarcity, less than half can get water
            base_bid = max(base_bid, DAILY_SALARY * 0.75, highest_prev_bid + 3.0)

    # Ensure bid is not negative and does not exceed budget
    final_bid = min(my_status['budget'], max(0.0, base_bid))
    
    # Final check for critical survival: if I NEED water, bid as high as possible within budget
    if my_status['hp'] <= 1 or my_status['no_water_days'] >= 1 or current_day >= EPISODE_DAYS - 1: # Last day or critical HP
        final_bid = min(my_status['budget'], max(final_bid, DAILY_SALARY - 1.0)) # Ensure max possible bid

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to secure water
    if not alive_opponents:
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

    # Base bid
    bid_amount = DAILY_SALARY * 0.5 # Default moderate bid

    # Aggressive bidding if HP is low
    if my_hp <= 2: # Critical HP
        bid_amount = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP
        bid_amount = DAILY_SALARY * 0.8
    elif my_hp <= 6 and current_day > EPISODE_DAYS / 2: # Mid-low HP in late game
        bid_amount = DAILY_SALARY * 0.7

    # React to opponent's previous high bids
    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponent bid very high
            bid_amount = max(bid_amount, highest_prev_bid * 1.05) # Try to slightly outbid
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Opponent bid moderately high
            bid_amount = max(bid_amount, highest_prev_bid + 5)

    # Adjust for competition vs supply
    available_water_units = int(current_supply // WATER_REQ)
    if available_water_units == 0: # No water available, bid 0 to save budget
        return 0.0
    
    if num_alive_opponents >= available_water_units: # High competition relative to supply
        if my_hp <= 5: # If I need water, bid aggressively
            bid_amount = max(bid_amount, DAILY_SALARY * 0.8)
        else: # If HP is good, maybe take a risk or bid moderately high
            bid_amount = max(bid_amount, DAILY_SALARY * 0.6)

    # Adjust for late game pressure
    if current_day >= EPISODE_DAYS - 2: # Last two days
        bid_amount = max(bid_amount, DAILY_SALARY * 0.9)
    elif current_day >= EPISODE_DAYS - 4: # Last four days
        bid_amount = max(bid_amount, DAILY_SALARY * 0.75)

    # Cap bid at my budget
    final_bid = min(my_budget, bid_amount)

    # Ensure a minimum bid if I desperately need water and budget allows
    if my_hp <= 3 and final_bid < DAILY_SALARY * 0.5 and my_budget >= DAILY_SALARY * 0.5:
        final_bid = min(my_budget, DAILY_SALARY * 0.5)

    # Ensure bid is not negative
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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid: a reasonable amount to secure water, considering my salary
    # In a "winner takes first" scenario, I need to be the highest.
    # A base of 50-60% of daily salary is a good starting point for competitive bidding.
    my_bid = DAILY_SALARY * 0.55

    # Aggressive bidding if HP is critical or I missed water yesterday
    if my_hp <= 2:
        my_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4:
        my_bid = DAILY_SALARY * 0.8
    elif my_no_water_days > 0: # If I missed water even with okay HP, I need to secure it
        my_bid = max(my_bid, DAILY_SALARY * 0.7)

    # Strategic adjustment based on opponent's highest bid from yesterday
    # If I'm not in a critical HP state (already bidding very high), 
    # try to outbid the highest opponent bid from yesterday with a small margin.
    if highest_prev_bid > 0 and my_hp > 2: # Only adjust if not already in max-bid mode
        # Aim to beat the highest previous bid, but not overpay excessively.
        # If my current calculated bid is lower than highest_prev_bid + a margin, raise it.
        competitive_bid = highest_prev_bid + 5 # Add a small buffer to win
        my_bid = max(my_bid, competitive_bid)
    elif highest_prev_bid == 0 and len(alive_opponents) > 0:
        # If no previous bids (e.g., day 1 or opponents didn't bid),
        # and there are opponents, bid reasonably high to establish presence.
        my_bid = max(my_bid, DAILY_SALARY * 0.6)

    # End-game aggression: Last few days, push harder for survival
    if current_day >= EPISODE_DAYS - 2: # Last 2 days (Day 9 and 10 assuming 1-indexed days)
        my_bid = max(my_bid, DAILY_SALARY * 0.9) # Be very aggressive

    # Ensure bid does not exceed available budget
    my_bid = min(my_budget, my_bid)

    # Ensure a minimum bid to be competitive, even if budget is low, unless it's literally 0.
    if my_budget > 0:
        my_bid = max(my_bid, DAILY_SALARY * 0.1) # Minimum floor bid
    else: # If budget is 0, bid 0.
        my_bid = 0.0

    return my_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid: Start with a moderate bid
    base_bid = DAILY_SALARY * 0.55 # Slightly above half salary

    # 1. Adjust bid based on my HP and no_water_days (survival priority)
    if my_hp <= 2 or my_no_water_days >= 1: # Critical HP or missed water yesterday
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.75
    elif my_hp <= 6: # Moderate HP
        base_bid = DAILY_SALARY * 0.65

    # 2. Adjust bid based on current supply and total demand
    total_water_needed_by_alive = WATER_REQ + sum(o['water_requirement'] for o in alive_opponents)
    
    # If supply is very low relative to demand, competition will be fierce
    if current_supply < total_water_needed_by_alive * 0.8: # Very tight supply
        base_bid *= 1.2 # Increase bid significantly
    elif current_supply < total_water_needed_by_alive: # Tight supply
        base_bid *= 1.1 # Increase bid
    elif current_supply > total_water_needed_by_alive * 1.5: # Abundant supply
        if my_hp > 5 and my_no_water_days == 0: # If healthy, can save
            base_bid *= 0.8 # Decrease bid

    # 3. Analyze opponent's yesterday's bids from previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        max_opp_bid_yesterday = max(yesterday_bids)
        avg_opp_bid_yesterday = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents were very aggressive yesterday
        if max_opp_bid_yesterday >= DAILY_SALARY * 0.8:
            if my_hp <= 4: # I need water, must compete
                base_bid = max(base_bid, max_opp_bid_yesterday + 10)
            elif current_supply < total_water_needed_by_alive: # Supply is tight
                base_bid = max(base_bid, max_opp_bid_yesterday + 5)
            else: # Healthy, abundant supply, maybe try to save a bit but still be competitive
                base_bid = max(base_bid, avg_opp_bid_yesterday + 1)
        # If opponents were very conservative yesterday
        elif max_opp_bid_yesterday <= DAILY_SALARY * 0.3:
            if my_hp > 6 and current_supply > total_water_needed_by_alive * 1.5: # Very healthy, abundant supply
                base_bid = min(base_bid, DAILY_SALARY * 0.25) # Try to save aggressively
            else: # Still ensure I get water
                base_bid = max(base_bid, avg_opp_bid_yesterday + 1)
        # Moderate opponent bids
        else:
            base_bid = max(base_bid, avg_opp_bid_yesterday + 1) # Bid slightly above average to secure water

    # 4. End-game strategy
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last 2 days
        if my_hp <= 3: # Critical for survival
            base_bid = max(base_bid, DAILY_SALARY * 1.0) # Bid full salary if needed
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.8) # Ensure survival for final days
    elif current_day <= 2 and num_alive_opponents > 1: # Early game, more opponents
        if my_hp > 7: # Healthy, try to conserve budget early
            base_bid = min(base_bid, DAILY_SALARY * 0.4)
        else: # Not so healthy, secure water
            base_bid = max(base_bid, DAILY_SALARY * 0.5)

    # Ensure bid is always positive and within budget
    final_bid = max(1.0, min(base_bid, my_budget))

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

    current_day = day_context['day']
    supply = day_context['supply']

    # --- Base Bid Calculation ---
    # Start with a moderately competitive bid
    base_bid = DAILY_SALARY * 0.5 # 75

    # Adjust base bid based on remaining budget and days, to prevent overspending too early
    remaining_days = EPISODE_DAYS - current_day + 1
    if remaining_days <= 0:
        remaining_days = 1 # Avoid division by zero
    
    projected_daily_spend = my_status['budget'] / remaining_days
    base_bid = min(base_bid, projected_daily_spend * 1.5) # Soft cap based on projected spend

    # --- Opponent Analysis ---
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid minimum to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Calculate total water needed by all alive agents
    total_water_needed_by_opponents = sum(o['water_requirement'] for o in alive_opponents)
    total_water_needed_by_all = total_water_needed_by_opponents + WATER_REQ

    # --- Adjust bid based on supply scarcity ---
    # If supply is less than total demand, competition will be high
    if supply < total_water_needed_by_all:
        scarcity_factor = 1.0 + (total_water_needed_by_all - supply) / total_water_needed_by_all
        base_bid *= scarcity_factor
    elif supply > total_water_needed_by_all + 5: # If supply is very abundant
        base_bid *= 0.7 # Bid lower to conserve

    # --- Adjust bid based on my HP and no-water days ---
    if my_status['hp'] <= 2: # Critical HP
        base_bid = max(base_bid, DAILY_SALARY * 0.95) # Bid very aggressively
    elif my_status['no_water_days'] > 0: # Missed water yesterday
        base_bid = max(base_bid, DAILY_SALARY * 0.75) # Bid high to get water

    # --- Adjust bid based on opponents' previous bids (yesterday's pressure) ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest previous bid was very high, react strongly
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 3: # If healthy, be competitive but don't overspend blindly
                base_bid = max(base_bid, highest_prev_bid * 0.95)
            else: # If not healthy, match or slightly exceed to survive
                base_bid = max(base_bid, highest_prev_bid + 5) # Add a small buffer
        else: # If previous bids were moderate, bid slightly above to win
            base_bid = max(base_bid, highest_prev_bid * 1.05) # Slightly outbid

    # Consider Eric specifically, as he is the strongest based on meta-round context
    eric_status = opponents_status.get('Eric')
    if eric_status and eric_status['alive']:
        eric_prev_trace = eric_status.get('previous_trace', {})
        if eric_prev_trace and eric_prev_trace.get('bid') is not None:
            eric_yesterday_bid = eric_prev_trace['bid']
            # If Eric's HP is low but budget is high, he's a significant threat
            if eric_status['hp'] <= 2 and eric_status['budget'] > DAILY_SALARY * 2: # High budget for desperation
                base_bid = max(base_bid, eric_yesterday_bid * 1.15) # Be more aggressive against a desperate, rich Eric
            # Ensure we are competitive against Eric generally
            base_bid = max(base_bid, eric_yesterday_bid * 1.03) # Slightly above Eric's last bid if he's active

    # Final bid must not exceed budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure bid is at least 0.0
    return max(0.0, final_bid)
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
    num_alive_opponents = len(alive_opponents)

    # Base bid, adjusted for HP
    if my_status['hp'] <= 2: # Critical HP
        bid_amount = DAILY_SALARY * 0.98 # Very aggressive to survive
    elif my_status['hp'] <= 5: # Low HP
        bid_amount = DAILY_SALARY * 0.90 # Aggressive
    else: # Healthy HP
        bid_amount = DAILY_SALARY * 0.75 # Moderate

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # Adjust bid based on highest previous opponent bid to ensure winning the single water unit.
        if highest_prev_bid >= DAILY_SALARY * 0.90: # Opponents were very aggressive yesterday
            if my_status['hp'] > 5: # Healthy, but competition is fierce
                bid_amount = max(bid_amount, highest_prev_bid + 2.0) # Slightly outbid
            else: # Low/critical HP, must win
                bid_amount = max(bid_amount, highest_prev_bid + 5.0) # Ensure win
        elif highest_prev_bid >= DAILY_SALARY * 0.70: # Moderately high bids yesterday
            bid_amount = max(bid_amount, highest_prev_bid + 3.0) # Try to outbid
        else: # Lower bids yesterday
            bid_amount = max(bid_amount, highest_prev_bid + 10.0) # Secure win with a larger margin

    # End game desperation
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] < 5: # Last 2 days, low HP
        bid_amount = max(bid_amount, my_status['budget'] * 0.95) # Bid almost everything to survive

    # If no opponents, or I'm the only one left, bid conservatively to save budget
    if num_alive_opponents == 0:
        bid_amount = min(my_status['budget'], DAILY_SALARY * 0.3)

    # Ensure bid is positive and within budget
    bid_amount = max(1.0, min(bid_amount, my_status['budget']))

    return bid_amount
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    bid_val = float(DAILY_SALARY)

    # Aggressiveness based on my HP
    if my_hp <= 2:
        bid_val *= 1.4 # Very aggressive
    elif my_hp <= 4:
        bid_val *= 1.2 # Aggressive
    else:
        bid_val *= 0.9 # Slightly conservative if HP is good, to save budget

    # Aggressiveness based on supply scarcity
    # Supply range [15, 25]. My WATER_REQ = 13.
    # If supply is 15-18, only one person can get 13 units. Very high competition.
    # If supply is 19-25, one person can get 13 units, and another can get 6-12 units. Still high competition for full 13.
    if current_supply < WATER_REQ + 6: # Very scarce, supply 15-18
        bid_val *= 1.3
    elif current_supply < WATER_REQ * 2: # Scarce, supply 19-25 (less than 2 full requirements)
        bid_val *= 1.1
    else: # Abundant (unlikely in this scenario with max supply 25 and my req 13)
        bid_val *= 0.8

    # Adjust based on opponent's previous bids
    strong_opponents_yesterday_bids = []
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                # Only consider bids that were somewhat significant relative to their salary
                if prev['bid'] >= opp_data['daily_salary'] * 0.5:
                    strong_opponents_yesterday_bids.append(prev['bid'])

    if strong_opponents_yesterday_bids:
        highest_prev_bid = max(strong_opponents_yesterday_bids)
        # If the highest bid was competitive, try to slightly exceed it
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            bid_val = max(bid_val, highest_prev_bid + 5.0) # Add a small buffer to win

    # Adjust for late game pressure
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        bid_val *= 1.15 # Be more aggressive to survive

    # Final bid must be within budget and above a minimum to participate meaningfully
    final_bid = min(my_budget, bid_val)
    final_bid = max(final_bid, DAILY_SALARY * 0.1)

    return final_bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to secure water and save budget.
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid based on my health and general strategy
    my_current_bid = DAILY_SALARY * 0.5 # Default moderate bid

    # Aggressiveness increases with lower HP
    if my_status['hp'] <= 2: # Critical HP
        my_current_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP
        my_current_bid = DAILY_SALARY * 0.75
    
    # If missed water recently, need to win
    if my_status['no_water_days'] > 0:
        my_current_bid = max(my_current_bid, DAILY_SALARY * 0.8)

    # Adjust bid based on opponent's previous bids and supply
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # Check for high competition (supply < total water needed by all active players)
        if day_context['supply'] < (num_alive_opponents + 1) * WATER_REQ:
            # High competition expected, bid aggressively
            if my_status['hp'] <= 4: # Low HP, must win
                my_current_bid = max(my_current_bid, highest_prev_bid + 5)
                my_current_bid = max(my_current_bid, DAILY_SALARY * 0.8) # Ensure a floor
            else: # Healthy HP, but still high competition, be competitive
                my_current_bid = max(my_current_bid, highest_prev_bid + 1)
                my_current_bid = max(my_current_bid, DAILY_SALARY * 0.6)
        else:
            # Supply is relatively ample, can be slightly less aggressive
            if my_status['hp'] <= 2: # Still bid high if critical, even with ample supply
                my_current_bid = max(my_current_bid, highest_prev_bid + 10)
            elif my_status['hp'] <= 4: # Low HP
                my_current_bid = max(my_current_bid, highest_prev_bid + 2)
            else: # Healthy HP, try to save money, but still aim to win if possible
                # Bid just above the highest previous bid if it's low, otherwise stick to current_bid
                if highest_prev_bid < DAILY_SALARY * 0.5:
                    my_current_bid = max(my_current_bid, highest_prev_bid + 1)
                # Ensure we don't underbid too much if others are bidding high
                my_current_bid = max(my_current_bid, DAILY_SALARY * 0.4)

    # Ensure the bid is not less than a very small amount to avoid issues
    my_current_bid = max(my_current_bid, 0.01)

    # Do not bid more than current budget
    final_bid = min(my_status['budget'], my_current_bid)
    
    return final_bid
"""
