# ============================================================
# Experiment: exp_054
# Agent: Cindy
# Source: exp_054
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    highest_prev_opp_bid = 0.0
    
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_opp_bid = max(highest_prev_opp_bid, prev['bid'])

    current_bid = 0.0

    if not alive_opponents:
        # No opponents, bid minimum to get water
        current_bid = 1.0 # Bid 1.0 to ensure water and save budget
    else:
        # Only one agent can get water in this scenario, making bidding highly competitive.
        if my_status['hp'] <= 2: # Critical HP
            # Bid very aggressively, ensuring to beat previous highest bid and a high base
            current_bid = max(DAILY_SALARY * 0.95, highest_prev_opp_bid + 5.0)
        elif my_status['hp'] <= 4: # Urgent HP
            # Bid aggressively, trying to win
            current_bid = max(DAILY_SALARY * 0.8, highest_prev_opp_bid + 2.0)
        else: # HP is relatively good
            # Bid competitively but with some budget consideration
            current_bid = max(DAILY_SALARY * 0.6, highest_prev_opp_bid + 1.0)
            
            # If budget is tight and HP is good, be slightly less aggressive
            if my_status['budget'] < DAILY_SALARY * 1.5 and my_status['hp'] > 5:
                current_bid = max(DAILY_SALARY * 0.5, highest_prev_opp_bid + 0.5)

    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], current_bid)
    
    # Ensure bid is at least 1.0 if we are trying to win and have budget
    if final_bid < 1.0 and my_status['budget'] >= 1.0 and alive_opponents:
        final_bid = 1.0
    elif final_bid < 0.0: # Safeguard against negative bids
        final_bid = 0.0

    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid low to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Calculate days remaining
    remaining_days = EPISODE_DAYS - day_context['day']

    # Determine if desperate for water
    is_desperate = my_status['hp'] <= 2 or my_status['no_water_days'] >= 1

    yesterday_bids = []
    eric_bid_yesterday = None

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            if opp['agent_id'] == "Eric":
                eric_bid_yesterday = prev['bid']

    # --- Bidding Logic ---
    bid_amount = DAILY_SALARY * 0.7 # Default moderate bid

    if is_desperate:
        bid_amount = DAILY_SALARY * 0.98 # Bid very high to ensure water
    elif yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If opponents were very aggressive yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 3 and remaining_days > EPISODE_DAYS / 2: # Early/mid-game, good HP
                bid_amount = DAILY_SALARY * 0.4 # Back off, save budget
            else:
                bid_amount = max(DAILY_SALARY * 0.75, highest_prev_bid + 5.0) # Compete, but not blindly overpay
        # If opponents were moderately aggressive
        else:
            # If Eric was the highest bidder and his bid was low (around his salary)
            # Eric's salary is likely 70, so < 90 is his range
            if eric_bid_yesterday is not None and highest_prev_bid == eric_bid_yesterday and highest_prev_bid < DAILY_SALARY * 0.6:
                bid_amount = eric_bid_yesterday + 5.0 # Just beat Eric
            else:
                # Try to slightly outbid the highest moderate bid
                bid_amount = max(DAILY_SALARY * 0.6, highest_prev_bid + 5.0)
    else:
        # Day 1 or no relevant previous bids
        if is_desperate:
            bid_amount = DAILY_SALARY * 0.95
        else:
            # On Day 1, or if previous bids are unavailable, start with a moderate bid.
            # If Eric is the only one, we can target him specifically.
            eric_is_alive = any(o['agent_id'] == "Eric" for o in alive_opponents)
            if eric_is_alive and len(alive_opponents) == 1:
                 bid_amount = 75.0 # Just beat Eric's likely 70
            else:
                 bid_amount = DAILY_SALARY * 0.7 # General moderate bid

    # Ensure bid does not exceed available budget
    return min(my_status['budget'], bid_amount)
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid strategy: Start with a moderately aggressive bid given the competition
    base_bid = DAILY_SALARY * 0.75

    # Adjust based on my HP
    if my_hp <= 2: # Critical HP, bid very aggressively
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 5: # Low HP, bid aggressively
        base_bid = DAILY_SALARY * 0.85
    # If HP is good (> 5), stick to base_bid or slightly less if conditions allow (but usually not with many players)

    # Incorporate opponent's yesterday bids from previous_trace
    yesterday_bids = []
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive'] and opp_data.get('previous_trace'):
            prev_bid = opp_data['previous_trace'].get('bid')
            if prev_bid is not None:
                yesterday_bids.append(prev_bid)

    # Adjust bid based on opponent's previous bids and competition
    if num_alive_opponents > 0:
        if yesterday_bids:
            max_opp_bid_yesterday = max(yesterday_bids)
            # If max opponent bid was higher than my current base, try to beat it slightly
            if max_opp_bid_yesterday >= base_bid * 0.9: # If their max bid was almost as high as my current base
                base_bid = max(base_bid, max_opp_bid_yesterday + 2) # Try to outbid by a small margin

            # If supply is very tight (e.g., only enough for one player) and multiple opponents, bid even higher
            if day_context['supply'] <= WATER_REQ * 1.2 and num_alive_opponents > 1: # Supply 15-16, very tight
                base_bid = max(base_bid, DAILY_SALARY * 0.9) # Ensure a high bid in tight situations

    # Consider remaining days and budget
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days == 0: # Last day, spend all if needed to survive
        return my_budget
    elif remaining_days <= 2: # Last couple of days, be more aggressive to ensure survival
        base_bid = max(base_bid, DAILY_SALARY * 0.9)

    # Ensure bid doesn't exceed budget or go below zero
    final_bid = min(base_bid, my_budget)
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
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    base_bid = DAILY_SALARY * 0.5

    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5:
        base_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] >= EPISODE_DAYS - day_context['day'] + 3:
        base_bid = DAILY_SALARY * 0.4

    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.7)
    elif remaining_days == 0:
        base_bid = max(base_bid, DAILY_SALARY * 0.99)

    num_potential_winners = int(day_context['supply'] // WATER_REQ)
    total_competitors = num_alive_opponents + 1

    if num_potential_winners < total_competitors:
        base_bid *= 1.15
    elif num_potential_winners >= total_competitors:
        base_bid *= 0.85

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 4:
                base_bid = max(base_bid, highest_prev_bid * 0.95)
            else:
                base_bid = max(base_bid, highest_prev_bid + 5.0)
        else:
            base_bid = max(base_bid, highest_prev_bid + 2.0)

    final_bid = max(0.0, min(my_status['budget'], base_bid))

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # Total days in a meta-round

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimally to save budget
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # --- Step 1: Determine a base bid based on my HP and day progression ---
    base_bid = DAILY_SALARY * 0.5 # Moderate starting point

    # Aggressive bidding if HP is low
    if my_hp <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4:
        base_bid = DAILY_SALARY * 0.8
    elif my_hp >= 8 and my_budget > DAILY_SALARY * 2: # If HP is good and budget allows, can be more conservative
        base_bid = DAILY_SALARY * 0.45

    # Increase bid pressure in late game
    days_left = EPISODE_DAYS - current_day
    if days_left <= 2 and my_hp < 5: # Critical end game and low HP
        base_bid = max(base_bid, DAILY_SALARY * 1.0) # Bid at least my salary
    elif days_left <= 3: # Approaching end game
        base_bid *= 1.1


    # --- Step 2: Adjust bid based on supply vs demand ---
    total_water_demand = WATER_REQ
    for opp in alive_opponents:
        total_water_demand += opp['water_requirement']

    # If supply is scarce, increase bid
    if current_supply < total_water_demand:
        # How much more water is demanded than supplied?
        shortage_ratio = total_water_demand / current_supply
        base_bid *= (1.0 + (shortage_ratio - 1.0) * 0.5) # Increase bid proportionally to scarcity, but not excessively

    # If supply is abundant, slightly reduce bid, but still aim to win
    elif current_supply >= total_water_demand * 1.5: # Abundant supply
        base_bid *= 0.85
    elif current_supply >= total_water_demand * 1.2: # Sufficient supply
        base_bid *= 0.95


    # --- Step 3: React to opponent's previous bids ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents were aggressive, match or slightly exceed their max bid, especially if I need water
        if max_yesterday_bid > DAILY_SALARY * 0.7 and my_hp < 7:
            base_bid = max(base_bid, max_yesterday_bid * 1.05)
        # If opponents were generally low, I might reduce my bid if my HP is good
        elif avg_yesterday_bid < DAILY_SALARY * 0.4 and my_hp > 5:
            base_bid = min(base_bid, avg_yesterday_bid * 1.2)
        # Otherwise, try to stay competitive around the average
        else:
            base_bid = max(base_bid, avg_yesterday_bid * 0.95)


    # --- Step 4: Final Adjustments and Constraints ---
    # Ensure a minimum bid to stay in contention, especially if water is critical
    min_competitive_bid = DAILY_SALARY * 0.1
    if my_hp <= 2:
        min_competitive_bid = DAILY_SALARY * 0.6 # Desperate bid floor
    elif my_no_water_days > 0: # If I missed water yesterday, I need it today
        min_competitive_bid = DAILY_SALARY * 0.5

    final_bid = max(min_competitive_bid, base_bid)

    # Ensure bid does not exceed current budget
    final_bid = min(final_bid, my_budget)

    # Ensure bid is not negative
    final_bid = max(0.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid very low to save budget.
    if not alive_opponents:
        return max(0.01, min(my_status['budget'], DAILY_SALARY * 0.1))

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid based on my HP
    base_bid = DAILY_SALARY * 0.65 # Default competitive bid

    if my_status['hp'] <= 2: # Very critical HP
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5: # Low HP
        base_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] >= 8: # Healthy HP, can afford to be more conservative
        base_bid = DAILY_SALARY * 0.55

    # Adjust based on supply scarcity
    # When supply is low, competition is higher. Increase bid up to 20%.
    supply_pressure_adjustment = (MAX_SUPPLY - day_context['supply']) / (MAX_SUPPLY - MIN_SUPPLY)
    base_bid *= (1 + supply_pressure_adjustment * 0.2)

    # Adjust bid based on opponents' previous highest bid
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        # If opponents were bidding high yesterday, we might need to bid slightly higher
        if max_yesterday_bid >= base_bid * 0.85: # If yesterday's max bid was already significant
            base_bid = max(base_bid, max_yesterday_bid + 5) # Ensure we are at least 5 higher than max, or keep our high bid

    # Ensure the bid doesn't exceed current budget and is at least 0.01
    final_bid = min(my_status['budget'], base_bid)
    return max(0.01, final_bid)
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

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    my_current_hp = my_status['hp']
    my_budget = my_status['budget']
    current_supply = day_context['supply']

    bid_very_aggressive = DAILY_SALARY * 0.98
    bid_aggressive = DAILY_SALARY * 0.9
    bid_high_moderate = DAILY_SALARY * 0.8
    bid_moderate = DAILY_SALARY * 0.7
    bid_low_moderate = DAILY_SALARY * 0.6
    bid_conservative = DAILY_SALARY * 0.4

    bid_amount = 0.0

    if not yesterday_bids:
        # Day 1 or no previous bids from opponents
        if my_current_hp <= 2:
            bid_amount = bid_aggressive
        elif my_current_hp <= 5:
            bid_amount = bid_high_moderate
        else:
            # If supply is tight, be more aggressive initially
            if current_supply < WATER_REQ * (len(alive_opponents) + 1):
                bid_amount = bid_high_moderate
            else:
                bid_amount = bid_moderate
    else:
        highest_prev_bid = max(yesterday_bids)

        if my_current_hp <= 2:
            bid_amount = max(bid_aggressive, highest_prev_bid + 1.5)
        elif my_current_hp <= 5:
            bid_amount = max(bid_high_moderate, highest_prev_bid + 1.5)
        else:
            # Healthy HP
            if highest_prev_bid >= DAILY_SALARY * 0.9: # Opponent bid very high
                if current_supply <= WATER_REQ + 2: # Very tight supply
                    bid_amount = max(bid_high_moderate, highest_prev_bid + 1.5)
                else:
                    # If supply is not extremely tight, and I'm healthy, conserve budget
                    bid_amount = bid_moderate
            else:
                # Opponent bid moderate or low
                bid_amount = max(bid_moderate, highest_prev_bid + 1.5)

    final_bid = min(my_budget, bid_amount)
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

    # If no opponents, bid minimally to save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    current_day = day_context['day']
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    # --- Base Bid Calculation ---
    # Start with a moderate bid
    bid = DAILY_SALARY * 0.7

    # Adjust based on HP
    if my_hp <= 2: # Critical HP
        bid = DAILY_SALARY * 0.98
    elif my_hp <= 4: # Low HP
        bid = max(bid, DAILY_SALARY * 0.9)
    elif my_no_water_days > 0: # Missed water recently
        bid = max(bid, DAILY_SALARY * 0.85)

    # Adjust based on supply scarcity
    total_agents_competing = num_alive_opponents + 1
    # Check if supply is very tight (less than 1 water_req per agent)
    if supply < WATER_REQ * total_agents_competing:
        # If supply is less than my requirement, it's a huge fight
        if supply < WATER_REQ: # This means only one agent can get water at most
            bid = max(bid, DAILY_SALARY * 0.99) # Bid almost full salary
        else:
            # Scale up bid based on how scarce water is relative to total demand
            scarcity_factor = 1.0 + (WATER_REQ * total_agents_competing - supply) / (WATER_REQ * total_agents_competing)
            bid = max(bid, DAILY_SALARY * min(scarcity_factor * 0.85, 0.95)) # Cap scarcity adjustment

    # Adjust based on day progression (late game pressure)
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        if my_hp <= 4:
            bid = max(bid, DAILY_SALARY * 0.98) # Very aggressive if low HP late game
        else:
            bid = max(bid, DAILY_SALARY * 0.85) # Still aggressive to survive
    elif current_day >= EPISODE_DAYS - 4: # Last 4 days
        bid = max(bid, DAILY_SALARY * 0.8)

    # --- Opponent Analysis from previous_trace ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If highest previous bid was very high, react aggressively
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            # Try to outbid by a small margin, but not excessively if my HP is good
            if my_hp > 5 and supply > WATER_REQ * 2: # Good HP and some abundance
                bid = max(bid, highest_prev_bid + 1.0)
            else: # Low HP or tight supply, need to win
                bid = max(bid, highest_prev_bid + 5.0) # Bid more aggressively
        elif avg_prev_bid >= DAILY_SALARY * 0.8:
            # If average bid was high, ensure my bid is competitive
            bid = max(bid, avg_prev_bid + 2.0)
        
        # If supply is abundant and my HP is good, try to conserve by bidding just above the highest previous bid
        # only if that bid was not excessively high.
        if my_hp > 6 and supply >= WATER_REQ * total_agents_competing * 1.2: # Abundant supply
            if highest_prev_bid < DAILY_SALARY * 0.8: # If opponents weren't super aggressive
                bid = min(bid, highest_prev_bid + 1.0) # Try to win cheaply
            else:
                bid = max(bid, DAILY_SALARY * 0.75) # Still maintain a decent bid

    # Ensure bid is within budget and non-negative
    final_bid = min(my_budget, max(0.01, bid)) # Bid at least 0.01

    return round(final_bid, 2)
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
    num_active_players = len(alive_opponents) + 1 # Including myself

    # Base bid: a percentage of my daily salary
    base_bid = DAILY_SALARY * 0.75

    # Adjust for low HP or no water days
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        base_bid = DAILY_SALARY * 0.95 # Bid aggressively for survival
    elif my_status['hp'] <= 4: # Medium low HP
        base_bid = DAILY_SALARY * 0.85

    # If no opponents, bid minimally to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Analyze yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Adjust bid based on opponent's previous high bid and supply
    # Supply-demand pressure
    supply_per_player_avg = day_context['supply'] / num_active_players
    
    if supply_per_player_avg < WATER_REQ: # High competition expected
        # If others bid high yesterday, match or slightly exceed to stay competitive
        if highest_prev_bid > DAILY_SALARY * 0.8: # Alex/David often bid this high
            bid_value = max(base_bid, highest_prev_bid + 5.0)
        else:
            bid_value = base_bid * 1.1 # Slightly higher than base in high competition
    else: # Enough water for everyone on average, potentially less competition
        if highest_prev_bid > DAILY_SALARY * 0.7:
            bid_value = max(base_bid, highest_prev_bid + 1.0) # Stay competitive but try to save
        else:
            bid_value = base_bid * 0.9 # Try to bid lower to save budget

    # Final adjustments
    # Ensure bid doesn't exceed budget
    final_bid = min(my_status['budget'], bid_value)
    
    # Ensure bid is at least a minimal amount if budget allows and I need water
    if final_bid < DAILY_SALARY * 0.1 and my_status['budget'] >= DAILY_SALARY * 0.1:
        final_bid = DAILY_SALARY * 0.1

    # Aggressive bidding towards the end of the meta-round
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days
        final_bid = min(my_status['budget'], max(final_bid, DAILY_SALARY * 0.9))
        if my_status['hp'] <= 3:
             final_bid = min(my_status['budget'], DAILY_SALARY * 1.05) # Even more aggressive

    # Ensure bid is never negative or zero if I have budget
    if final_bid <= 0.0 and my_status['budget'] > 0.0:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.05) # Smallest possible bid to stay in game if budget is low
    if final_bid <= 0.0 and my_status['budget'] == 0.0:
        return 0.0 # Cannot bid if no budget

    return round(final_bid, 2)
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If I'm the only one left, bid minimum to get water
    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid: a fraction of daily salary, adjusted by supply
    # If supply is low (closer to MIN_SUPPLY), bid higher. If high (closer to MAX_SUPPLY), bid lower.
    # supply_factor ranges from 0 (MIN_SUPPLY) to 1 (MAX_SUPPLY)
    supply_factor = (day_context['supply'] - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    # adjusted_supply_factor ranges from 1 (MIN_SUPPLY) to 0 (MAX_SUPPLY)
    adjusted_supply_factor = 1 - supply_factor

    # Bid ranges from 0.4 * DAILY_SALARY (max supply) to 0.8 * DAILY_SALARY (min supply)
    base_bid = DAILY_SALARY * 0.4 + (adjusted_supply_factor * DAILY_SALARY * 0.4)
    
    current_bid = base_bid

    # React to yesterday's highest bid from opponents
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents are bidding very high (e.g., Eric/David)
        if highest_prev_bid >= DAILY_SALARY * 0.8: # e.g., 120
            if my_status['hp'] > 3: # If my HP is good, be competitive but not overly aggressive
                current_bid = max(current_bid, highest_prev_bid * 1.05)
            else: # My HP is low, must win
                current_bid = max(current_bid, highest_prev_bid * 1.1)
        elif highest_prev_bid < DAILY_SALARY * 0.4: # If opponents bid very low
            # Try to save money if possible, but still secure water with a minimum reasonable bid
            current_bid = min(current_bid, highest_prev_bid + 5.0)
            current_bid = max(current_bid, DAILY_SALARY * 0.3) # Ensure a minimum reasonable bid
        else: # Moderate bids from opponents
            current_bid = max(current_bid, highest_prev_bid + 1.0) # Bid slightly above to win

    # Critical survival logic: if HP is very low, bid aggressively
    if my_status['hp'] <= 2:
        current_bid = max(current_bid, DAILY_SALARY * 0.95) # Almost full salary to ensure survival
    elif my_status['hp'] <= 4: # Medium low HP
        current_bid = max(current_bid, DAILY_SALARY * 0.8)

    # Ensure bid doesn't exceed budget
    final_bid = min(my_status['budget'], current_bid)

    # Ensure bid is at least 1 if I have budget
    if final_bid < 1.0 and my_status['budget'] >= 1.0:
        final_bid = 1.0
    elif final_bid < 0: # If budget is negative (shouldn't happen with min() check, but for safety)
        final_bid = 0.0

    return final_bid
"""
