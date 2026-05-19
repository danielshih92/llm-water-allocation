# ============================================================
# Experiment: exp_117
# Agent: Cindy
# Source: exp_117
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

    # Default bid based on HP and general competitiveness
    bid_amount = 0

    if my_status['hp'] <= 2: # Critical HP, must win
        bid_amount = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP, prioritize winning
        bid_amount = DAILY_SALARY * 0.7
    else: # Good HP, try to save money
        bid_amount = DAILY_SALARY * 0.4

    # Adjust bid based on number of opponents
    if num_alive_opponents == 0:
        return min(my_status['budget'], 1) # Bid minimum to secure water
    elif num_alive_opponents == 1:
        # Direct competition, slightly increase base bid
        bid_amount *= 1.05
    else: # Multiple opponents, slight increase for competition
        bid_amount *= 1.02

    # Adjust bid based on supply scarcity
    # Estimate total water needed by all active agents
    estimated_total_demand = (num_alive_opponents + 1) * WATER_REQ
    current_supply = day_context['supply']

    if current_supply < estimated_total_demand:
        # Supply is scarce, increase bid
        # Calculate scarcity ratio: 0 if enough for everyone, 1 if just enough for one
        denominator = estimated_total_demand - WATER_REQ
        if denominator <= 0: # Should not happen if num_alive_opponents > 0
            scarcity_ratio = 1 # Extreme scarcity
        else:
            scarcity_ratio = max(0, (estimated_total_demand - current_supply) / denominator)
        bid_amount *= (1 + scarcity_ratio * 0.2) # Up to 20% increase based on scarcity
    elif current_supply > estimated_total_demand + WATER_REQ * 0.5: # If supply is significantly more than needed
        # Supply is abundant, decrease bid
        bid_amount *= 0.9 # 10% decrease

    # Incorporate yesterday's bids if available (as per example structure)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents bid very high yesterday, react to it
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] <= 3: # If my HP is low, I must be aggressive
                bid_amount = max(bid_amount, highest_prev_bid + 2) # Bid slightly higher
            else: # If HP is good, try to not overbid too much
                bid_amount = max(bid_amount, highest_prev_bid * 0.95) # Still competitive
        elif highest_prev_bid <= DAILY_SALARY * 0.3: # If opponents bid very low
             if my_status['hp'] >= 5: # If HP is good, try to win cheaply
                bid_amount = min(bid_amount, highest_prev_bid + 1)
             else: # If HP is not great, ensure win but don't overpay
                bid_amount = max(bid_amount, highest_prev_bid + 1)
        else: # Moderate bids yesterday
            bid_amount = max(bid_amount, highest_prev_bid * 1.02) # Slightly above to win

    # Ensure bid is within budget and at least 1 (unless budget is 0)
    final_bid = max(1, min(my_status['budget'], bid_amount))

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

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    bid = DAILY_SALARY * 0.5 

    if my_hp <= 2 or my_no_water_days >= 1:
        bid = DAILY_SALARY * 1.2 
        if current_day >= EPISODE_DAYS - 2:
            bid = DAILY_SALARY * 1.5 
    elif my_hp <= 5:
        bid = DAILY_SALARY * 0.9 
    elif current_day >= EPISODE_DAYS - 3:
        bid = DAILY_SALARY * 1.1 

    if highest_prev_bid > 0:
        if bid <= highest_prev_bid:
            bid = highest_prev_bid + (DAILY_SALARY * 0.05) 
            if my_hp <= 3:
                bid = highest_prev_bid + (DAILY_SALARY * 0.1)

    bid = max(bid, DAILY_SALARY * 0.7)

    final_bid = min(my_budget, bid)

    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid: Start with a reasonable fraction of daily salary
    bid = DAILY_SALARY * 0.5

    # 1. Adjust bid based on my HP and no_water_days (desperation)
    if my_status['hp'] <= 3: # Critical HP
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 6: # Low HP
        bid = DAILY_SALARY * 0.8
    elif my_status['no_water_days'] > 0: # Missed water yesterday, need to get it today
        bid = DAILY_SALARY * 0.75

    # 2. Adjust bid based on supply vs demand
    total_water_needed = (num_alive_opponents + 1) * WATER_REQ
    if day_context['supply'] < total_water_needed:
        # Scarcity: increase bid
        bid *= 1.1 # Increase by 10%
        if my_status['hp'] <= 7: # If also somewhat desperate, ensure higher bid
            bid = max(bid, DAILY_SALARY * 0.85)
    elif day_context['supply'] >= total_water_needed * 1.5:
        # Abundance: can be more conservative
        bid *= 0.9 # Decrease by 10%

    # 3. React to yesterday's opponent bids (previous_trace)
    yesterday_bids = []
    david_is_alive = False
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            if opp_id == 'David':
                david_is_alive = True
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents bid high yesterday, react by bidding slightly higher
        if highest_prev_bid >= DAILY_SALARY * 0.7:
            if my_status['hp'] <= 5: # Very desperate, must win
                bid = max(bid, highest_prev_bid + 15)
            else: # Not critical, but stay competitive
                bid = max(bid, highest_prev_bid + 7)
        # If opponents bid low, try to win cheaply but don't risk losing if I need water
        elif highest_prev_bid < DAILY_SALARY * 0.4 and my_status['hp'] > 7:
            bid = min(bid, highest_prev_bid + 5) # Try to win with small margin if not desperate

    # 4. Specific consideration for David (based on meta-round context)
    # David is a strong player, likely higher salary or very aggressive. 
    # If David is alive and competition is high or I'm low on HP, bid very strongly.
    if david_is_alive:
        if day_context['supply'] < total_water_needed or my_status['hp'] <= 7:
            bid = max(bid, DAILY_SALARY * 0.9) # Ensure a very strong bid against David

    # Final bid must be within budget and non-negative
    final_bid = min(my_status['budget'], bid)
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1) if my_status['budget'] > 0 else 0.01

    num_possible_winners = int(day_context['supply'] // WATER_REQ)
    if num_possible_winners == 0:
        num_possible_winners = 1 

    yesterday_bids = []
    eric_yesterday_bid = 0.0
    eric_is_alive = False
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
            if opp_id == 'Eric':
                eric_is_alive = True
                if prev and prev.get('bid') is not None:
                    eric_yesterday_bid = prev['bid']

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    base_bid = DAILY_SALARY * 0.4

    my_hp_low = my_status['hp'] <= 2
    late_game = day_context['day'] >= int(EPISODE_DAYS * 0.7) 

    if my_hp_low:
        base_bid = DAILY_SALARY * 0.9
    elif late_game:
        base_bid = DAILY_SALARY * 0.7

    current_bid = base_bid

    if num_possible_winners == 1:
        if eric_is_alive and eric_yesterday_bid > 0:
            if my_hp_low or late_game:
                current_bid = max(current_bid, eric_yesterday_bid + 5, DAILY_SALARY * 0.95)
            else:
                current_bid = max(current_bid, eric_yesterday_bid + 2)
        else:
            current_bid = max(current_bid, highest_prev_bid + 3)
    elif num_possible_winners >= 2:
        if highest_prev_bid > 0:
            current_bid = max(current_bid, highest_prev_bid * 0.9 + 1)
        if eric_is_alive and eric_yesterday_bid > 0:
             current_bid = max(current_bid, eric_yesterday_bid * 0.7)

    final_bid = min(my_status['budget'], current_bid)
    return max(0.01, final_bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta_round_state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimum to conserve budget.
    if not alive_opponents:
        return min(my_status['budget'], 1)

    # Initialize base bid
    base_bid = DAILY_SALARY * 0.5 # A reasonable starting point

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Adjust base bid based on yesterday's highest bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Bid slightly above the highest previous bid to be competitive
        base_bid = max(base_bid, highest_prev_bid + 5)
    else:
        # If no previous bids are available (e.g., Day 1 or opponents reset),
        # use a default competitive bid.
        base_bid = max(base_bid, DAILY_SALARY * 0.6)

    # Desperation factor based on HP and no_water_days
    if my_status['hp'] <= 1 or my_status['no_water_days'] > 0:
        base_bid = max(base_bid, DAILY_SALARY * 0.95) # Very aggressive if critical
    elif my_status['hp'] <= 3:
        base_bid = max(base_bid, DAILY_SALARY * 0.8) # Aggressive if low HP

    # Supply vs Demand factor
    available_water_units = int(day_context['supply'] // WATER_REQ)
    num_active_players = len(alive_opponents) + 1 # Including myself

    if available_water_units < num_active_players:
        # Supply is tight, competition will be fierce
        base_bid = max(base_bid, DAILY_SALARY * 0.85)
    elif available_water_units >= num_active_players * 1.5:
        # Abundant supply, could potentially bid less, but still stay competitive
        # to ensure water and manage budget.
        base_bid = min(base_bid, DAILY_SALARY * 0.7)
    
    # End game pressure
    # If it's near the end of the episode and HP is low, bid very aggressively
    if day_context['day'] >= EPISODE_DAYS - 2 and my_status['hp'] <= 3:
        base_bid = max(base_bid, DAILY_SALARY * 1.05) # Willing to slightly overspend salary

    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure bid is at least 1 if budget allows
    final_bid = max(1, final_bid)

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

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_competitors = len(alive_opponents) + 1 # Myself + alive opponents

    # --- Base Bid Strategy ---
    # Start with a moderate bid, aiming to save budget but also secure water
    base_bid = DAILY_SALARY * 0.6 # 90

    # --- Adjust based on HP ---
    # If HP is critical, bid very high
    if my_hp <= 2:
        base_bid = DAILY_SALARY * 0.95 # 142.5
    elif my_hp <= 4 and my_budget > DAILY_SALARY: # Low HP but not critical, try to secure
        base_bid = DAILY_SALARY * 0.8 # 120

    # --- Adjust based on Supply Scarcity ---
    # If supply is very low, competition will be fierce
    if current_supply < WATER_REQ * num_competitors:
        if current_supply < WATER_REQ * 1.5: # Very tight supply, e.g., 15-19 for 2 people
            base_bid = max(base_bid, DAILY_SALARY * 0.85) # 127.5
        elif current_supply < WATER_REQ * 2: # Tight supply, e.g., 20-25 for 2 people
            base_bid = max(base_bid, DAILY_SALARY * 0.75) # 112.5

    # --- React to Opponents' Yesterday Bids ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were aggressive yesterday, I need to be competitive
        if highest_prev_bid >= DAILY_SALARY * 0.7: # If yesterday's max bid was high (>=105)
            # Bid slightly above the highest previous bid, but not excessively
            base_bid = max(base_bid, highest_prev_bid + 5.0)
        elif highest_prev_bid < DAILY_SALARY * 0.4 and my_hp > 5: # If they bid low and I'm healthy
            # Try to get water cheaper
            base_bid = min(base_bid, highest_prev_bid + 10.0) # Bid slightly above to win
            base_bid = max(base_bid, DAILY_SALARY * 0.3) # Ensure a minimum reasonable bid

    # --- End Game Strategy ---
    # If it's late in the game and I have budget, be more aggressive to survive
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_hp < 5: # Last 2 days, low HP
        base_bid = max(base_bid, DAILY_SALARY * 0.9) # 135
    elif remaining_days <= 2 and my_budget > DAILY_SALARY * 2: # Last 2 days, good budget
        base_bid = max(base_bid, DAILY_SALARY * 0.8) # 120 (can afford to be aggressive)

    # --- Final Bid Calculation ---
    # Ensure bid does not exceed current budget
    final_bid = min(base_bid, my_budget)

    # Ensure a minimum bid if budget allows and I need water
    if final_bid < 10.0 and my_hp < 5 and my_budget > 10.0:
        final_bid = 10.0 # Don't bid 0 if I need water and can afford something small

    # Ensure bid is at least 0
    final_bid = max(0.0, final_bid)

    return float(final_bid)
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

    # Base bid calculation
    base_bid = DAILY_SALARY * 0.75 # Start with a reasonable bid

    # Adjust bid based on my HP and no_water_days
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        base_bid = DAILY_SALARY * 0.95 # Critical survival bid
    elif my_status['hp'] <= 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.9) # Low HP, be aggressive

    # Adjust bid based on current day (later days, be more aggressive)
    current_day = day_context['day']
    if current_day >= EPISODE_DAYS - 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.98) # Very late game, maximize survival chance
    elif current_day >= EPISODE_DAYS - 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.9) # Late game, increase aggression

    # Opponent analysis from previous_trace
    yesterday_bids = []
    strong_opponent_bids = []
    
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
                # Identify strong opponents (e.g., Eric or consistently high bidders)
                if opp_id == "Eric" or prev['bid'] >= DAILY_SALARY * 0.85:
                    strong_opponent_bids.append(prev['bid'])

    if strong_opponent_bids:
        highest_strong_bid = max(strong_opponent_bids)
        base_bid = max(base_bid, highest_strong_bid + 2.0) # Slightly outbid strong opponents
    elif yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.7:
            base_bid = max(base_bid, highest_prev_bid + 1.0) # React to general high bids
        else:
            base_bid = min(base_bid, DAILY_SALARY * 0.7) # Conserve if bids are low

    # Adjust for supply scarcity
    # Calculate total water needed by all alive agents
    total_water_needed_by_all = WATER_REQ # For Cindy
    for opp in alive_opponents:
        total_water_needed_by_all += opp['water_requirement']

    available_water_units = int(day_context['supply'])

    if available_water_units < total_water_needed_by_all:
        # If supply is less than total demand, increase bid pressure
        scarcity_factor = (total_water_needed_by_all / available_water_units) if available_water_units > 0 else 2.0
        base_bid = base_bid * min(1.1, scarcity_factor) # Cap multiplier to avoid excessive bids

    # Final bid must be within budget and non-negative.
    final_bid = min(my_status['budget'], base_bid)
    final_bid = max(0.0, final_bid)

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

    current_day = day_context['day']
    my_budget = my_status['budget']
    my_hp = my_status['hp']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    eric_status = opponents_status.get('Eric')
    eric_prev_bid = 0.0
    if eric_status and eric_status['alive'] and eric_status.get('previous_trace'):
        eric_prev_bid = eric_status['previous_trace'].get('bid', 0.0)

    # Base bid strategy based on my HP
    if my_hp <= 2:
        target_bid = DAILY_SALARY * 1.5 # Critical HP, bid very aggressively
    elif my_hp <= 5:
        target_bid = DAILY_SALARY * 1.2 # Low HP, bid aggressively
    else:
        target_bid = DAILY_SALARY * 0.8 # Default bid, try to conserve budget

    # Adjust bid based on Eric's previous behavior
    if eric_prev_bid > DAILY_SALARY * 0.9: # If Eric was aggressive yesterday
        target_bid = max(target_bid, eric_prev_bid + 5.0)
    elif eric_prev_bid > 0.0: # If Eric bid, but not extremely high
        target_bid = max(target_bid, eric_prev_bid * 1.05)

    # Budget management: Don't spend more than what's reasonable for the remaining days
    remaining_days = EPISODE_DAYS - current_day + 1
    if remaining_days > 0:
        sustainable_daily_bid = my_budget / remaining_days
        if my_hp > 2:
            if target_bid > sustainable_daily_bid * 1.2:
                target_bid = min(target_bid, sustainable_daily_bid * 1.1)

    # Final check: ensure bid does not exceed available budget
    final_bid = min(my_budget, target_bid)
    
    # Ensure a minimum bid if I need water and my budget allows
    if final_bid < DAILY_SALARY * 0.3 and my_hp < 10:
        final_bid = max(final_bid, DAILY_SALARY * 0.3)
    
    if final_bid < 1.0 and my_budget > 0 and my_hp < 10:
        final_bid = 1.0

    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    base_bid = DAILY_SALARY * 0.5 # Default starting bid

    # Check for no alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        # If no opponents, bid minimum to get water
        return min(my_status['budget'], WATER_REQ * 1.0)

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP
        base_bid = DAILY_SALARY * 1.2 # Bid aggressively
    elif my_status['hp'] <= 5: # Low HP
        base_bid = DAILY_SALARY * 0.9 # Bid high
    elif my_status['hp'] >= 8: # Good HP, can afford to save a bit if not critical
        base_bid = DAILY_SALARY * 0.6 # Moderate bid

    # Adjust bid based on day progression
    current_day = day_context['day']
    if current_day >= EPISODE_DAYS - 2: # Last few days, increase desperation
        base_bid = max(base_bid, DAILY_SALARY * 1.0) # At least daily salary
    elif current_day >= EPISODE_DAYS / 2: # Mid-game, slightly more aggressive
        base_bid = max(base_bid, DAILY_SALARY * 0.75)

    # Adjust bid based on supply scarcity
    current_supply = day_context['supply']
    # If supply is very tight (e.g., only enough for one agent or barely more)
    if current_supply <= WATER_REQ + 5: # Supply <= 18
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    elif current_supply <= WATER_REQ + 10: # Supply <= 23, still competitive
        base_bid = max(base_bid, DAILY_SALARY * 0.7)

    # Analyze opponent's previous bids to react
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace')
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents bid very high, I might need to match or slightly exceed
        if highest_prev_bid > base_bid:
            base_bid = highest_prev_bid + 5 # Try to outbid by a small margin
        # If opponents bid low, I can try to save, but ensure I get water
        elif highest_prev_bid < DAILY_SALARY * 0.4 and my_status['hp'] > 5:
            base_bid = min(base_bid, highest_prev_bid + 10) # Don't overbid
            
    # Final bid must be capped by budget and be at least 0
    final_bid = max(0.0, min(base_bid, my_status['budget']))

    # Ensure bid is at least 1 if I really need water and have budget
    if my_status['hp'] < EPISODE_DAYS and final_bid == 0 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], 1.0) # Bid minimum to stay alive

    return final_bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid to ensure survival and budget management
    base_bid = DAILY_SALARY * 0.6 # Default moderate bid (90)

    # 1. HP-based adjustment: Prioritize survival if HP is low
    if my_status['hp'] <= 2: # Critical HP
        base_bid = DAILY_SALARY * 1.1 # Very aggressive (165)
    elif my_status['hp'] <= 4: # Low HP
        base_bid = max(base_bid, DAILY_SALARY * 0.9) # Aggressive (135)

    # 2. Day-based adjustment: Increase aggression on later days
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: # Last 2 days
        base_bid = max(base_bid, DAILY_SALARY * 1.0) # Very high bid (150)
    elif remaining_days <= 4: # Last 4 days
        base_bid = max(base_bid, DAILY_SALARY * 0.85) # High bid (127.5)

    # 3. Opponent `previous_trace` analysis: React to yesterday's bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were bidding very high, try to outbid them
        if highest_prev_bid >= DAILY_SALARY * 0.9: # e.g., >= 135
            base_bid = max(base_bid, highest_prev_bid + 5) # Try to outbid by a small margin
        # If opponents were bidding moderately high
        elif highest_prev_bid >= DAILY_SALARY * 0.7: # e.g., >= 105
            base_bid = max(base_bid, highest_prev_bid + 2)
        # If opponents were bidding low, try to win cheaply but don't go too low
        else:
            base_bid = max(base_bid, min(highest_prev_bid + 1, DAILY_SALARY * 0.5))
    else:
        # If no previous bids (e.g., day 1 or no active opponents with trace),
        # and if there are still opponents, ensure a competitive bid based on supply
        if num_alive_opponents > 0 and day_context['day'] == 1: # Only for day 1 initial competition
            # If supply is low, competition is likely high
            if day_context['supply'] <= MIN_SUPPLY + 3: # supply <= 18
                base_bid = max(base_bid, DAILY_SALARY * 0.75) # 112.5

    # 4. Final bid calculation: Ensure it doesn't exceed budget and is at least 1 if possible
    final_bid = min(my_status['budget'], base_bid)

    if final_bid <= 0 and my_status['budget'] > 0:
        return min(my_status['budget'], 1.0) # Bid 1 to stay in game if budget allows and calculated bid is 0
    return final_bid
"""
