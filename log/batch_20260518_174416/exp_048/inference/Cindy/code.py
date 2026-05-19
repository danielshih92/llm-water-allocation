# ============================================================
# Experiment: exp_048
# Agent: Cindy
# Source: exp_048
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
    num_total_agents_needing_water = num_alive_opponents + 1 # Including myself

    current_supply = day_context['supply']

    bid_amount = 0.0

    # Strategy based on HP and competition
    if num_alive_opponents == 0:
        # No opponents, bid very low to save budget
        bid_amount = DAILY_SALARY * 0.1
    elif my_status['hp'] <= 1:
        # Critical HP, bid very aggressively to survive
        bid_amount = DAILY_SALARY * 0.95
    elif my_status['hp'] == 2:
        # Low HP, bid aggressively
        bid_amount = DAILY_SALARY * 0.7
    else:
        # Healthy HP (3 or more)
        # Check if supply is enough for everyone
        if current_supply >= WATER_REQ * num_total_agents_needing_water:
            # Abundant supply, bid moderately low
            bid_amount = DAILY_SALARY * 0.4
        else:
            # Scarce supply, bid moderately high to secure water
            bid_amount = DAILY_SALARY * 0.6
    
    # Ensure bid does not exceed budget
    return min(my_status['budget'], bid_amount)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)
    num_total_players = num_alive_opponents + 1

    # Base bid - aiming for a certain percentage of daily salary
    base_bid_percentage = 0.75 
    base_bid = DAILY_SALARY * base_bid_percentage

    # Adjust base bid based on supply scarcity
    scarcity_factor = (MAX_SUPPLY - current_supply) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_adjustment = (scarcity_factor * 0.2 - 0.1) * DAILY_SALARY
    base_bid += supply_adjustment
    
    # Ensure base_bid is not too low to be competitive
    base_bid = max(base_bid, DAILY_SALARY * 0.4)

    # Aggressiveness based on my HP and no_water_days
    if my_no_water_days > 0 or my_hp <= 2:
        # Critical state, bid very aggressively
        return min(my_budget, DAILY_SALARY * 0.95 + (my_no_water_days * 10))
    elif my_hp <= 5:
        # Vulnerable state, bid aggressively, ensure it's at least 80% of salary
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    
    # Adjust bid based on opponent's previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents are bidding very high
        if max_prev_bid >= DAILY_SALARY * 0.8:
            if my_hp > 7:
                # If healthy, try to bid slightly below max to save budget
                base_bid = max(base_bid, max_prev_bid * 0.95)
            else:
                # If not healthy, bid slightly above max to secure water
                base_bid = max(base_bid, max_prev_bid + 5)
        # If opponents are generally bidding low
        elif avg_prev_bid <= DAILY_SALARY * 0.5:
            if my_hp > 7:
                # If healthy, try to save some budget by bidding lower
                base_bid = min(base_bid, DAILY_SALARY * 0.6)
            else:
                # If not healthy, maintain a reasonable bid to ensure water
                base_bid = max(base_bid, DAILY_SALARY * 0.65)

    # Adjust based on remaining days and budget for end-game push
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last days, be more aggressive if survival is at stake
        if my_hp <= 10: # If HP is not full, prioritize survival
            base_bid = max(base_bid, DAILY_SALARY * 0.9)

    # Ensure bid does not exceed budget
    final_bid = min(my_budget, base_bid)

    # Ensure bid is at least 1 to participate
    return max(1.0, final_bid)
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid: a strong starting point, slightly below average of strong opponents
    base_bid = DAILY_SALARY * 0.85

    # Adjust bid based on my HP
    if my_hp <= 2: # Critical HP, bid very aggressively
        base_bid = DAILY_SALARY * 1.1
    elif my_hp <= 5: # Low HP, bid aggressively
        base_bid = DAILY_SALARY * 0.98
    elif my_hp >= 8: # Healthy HP, can be slightly more conservative but still competitive
        base_bid = DAILY_SALARY * 0.75

    # Analyze opponent's previous bids from yesterday
    highest_prev_competitive_bid = 0.0
    num_competitive_opponents = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            # Consider bids above a certain threshold as competitive (e.g., > 50% of daily salary)
            if prev['bid'] > DAILY_SALARY * 0.5:
                highest_prev_competitive_bid = max(highest_prev_competitive_bid, prev['bid'])
                num_competitive_opponents += 1

    # React to competitive bids
    if highest_prev_competitive_bid > 0:
        # If supply is tight (less than 2x my requirement) AND there are competitive opponents
        # OR if my HP is low, try to outbid the highest previous bid.
        if (current_supply < WATER_REQ * 2 and num_competitive_opponents >= 1) or my_hp <= 5:
            base_bid = max(base_bid, highest_prev_competitive_bid + 5.0) # Bid slightly higher
        else:
            # If supply is more abundant or my HP is good, stay competitive but don't blindly overspend
            base_bid = max(base_bid, highest_prev_competitive_bid * 0.98) # Slightly below or at their bid

    # Adjust bid for end game scenarios
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last 2 days
        if my_hp <= 5: # Desperate for water, bid very high
            base_bid = max(base_bid, DAILY_SALARY * 1.2)
        elif my_budget > DAILY_SALARY * 0.5: # Have some budget left, secure win
            base_bid = max(base_bid, DAILY_SALARY * 1.0)
    elif remaining_days <= 4: # Mid-late game
        if my_hp <= 3: # Need to survive
            base_bid = max(base_bid, DAILY_SALARY * 1.05)

    # Consider supply vs. demand: If supply is barely enough for one person, and I need water, bid very high
    if current_supply < WATER_REQ * 1.2 and my_hp <= 5: # Very tight supply and low HP
        base_bid = max(base_bid, DAILY_SALARY * 1.15)

    # Final bid must not exceed budget
    final_bid = min(my_budget, base_bid)

    # Ensure bid is not negative, and if budget is very low, make a minimal bid if desperate
    if final_bid <= 0 and my_hp <= 5 and my_budget > 0:
        final_bid = min(my_budget, DAILY_SALARY * 0.1) # A last ditch effort

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

    day = day_context['day']
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    base_bid = DAILY_SALARY * 0.65

    # Adjust bid based on my HP
    if my_hp <= 1:
        base_bid = DAILY_SALARY * 1.05
    elif my_hp == 2:
        base_bid = DAILY_SALARY * 0.9
    elif my_hp == 3:
        base_bid = DAILY_SALARY * 0.75

    # Adjust if I haven't received water recently
    if no_water_days > 0:
        base_bid += DAILY_SALARY * 0.15

    # Adjust for late game pressure
    remaining_days = EPISODE_DAYS - day + 1
    if remaining_days <= 3:
        base_bid += DAILY_SALARY * 0.2
    elif remaining_days <= 5:
        base_bid += DAILY_SALARY * 0.1

    # Analyze yesterday's bids from opponents
    yesterday_bids = []
    opponent_salaries = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
        opponent_salaries.append(opp['daily_salary'])

    max_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
    
    avg_opponent_salary = sum(opponent_salaries) / num_alive_opponents if num_alive_opponents > 0 else DAILY_SALARY

    # Adjust bid based on opponent's previous aggression
    if max_yesterday_bid > 0:
        if max_yesterday_bid > avg_opponent_salary * 0.9:
            if my_hp <= 2:
                base_bid = max(base_bid, max_yesterday_bid + 10)
            else:
                base_bid = max(base_bid, max_yesterday_bid + 2)
        elif max_yesterday_bid > avg_opponent_salary * 0.6:
            base_bid = max(base_bid, max_yesterday_bid + 1)
        elif max_yesterday_bid < avg_opponent_salary * 0.5 and my_hp >= 3:
            base_bid = min(base_bid, max_yesterday_bid + 5)
            base_bid = max(base_bid, DAILY_SALARY * 0.3)

    # Given my WATER_REQ=13 and supply_range [15,25], I'm always competing for effectively one unit.
    # So, competition is always high for my water requirement.
    # This is implicitly handled by the base bid and HP/day adjustments.

    final_bid = min(my_budget, base_bid)
    final_bid = max(0.0, final_bid)

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

    # 1. Default bid - a reasonable starting point
    bid = DAILY_SALARY * 0.5

    if not alive_opponents:
        # Bid very low if no competition, just to secure water cheaply
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # 2. Adjust based on Opponent's Yesterday Bids (sets a competitive floor)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents were very aggressive
            bid = max(bid, highest_prev_bid * 1.05)
        elif highest_prev_bid >= DAILY_SALARY * 0.4: # Opponents were moderately aggressive
            bid = max(bid, highest_prev_bid + 5.0)
        else: # Opponents were very conservative
            bid = max(bid, highest_prev_bid + 1.0)

    # 3. Adjust for Supply/Demand (can lower bid if abundant, increase if scarce)
    total_water_needed_by_all = WATER_REQ
    for opp in alive_opponents: 
        total_water_needed_by_all += opp['water_requirement']

    if day_context['supply'] >= total_water_needed_by_all:
        # Abundant supply, if healthy, try to get water cheaper
        if my_status['hp'] > 3:
            bid = min(bid, DAILY_SALARY * 0.4)
    else:
        # Scarce supply, ensure bid is competitive
        if my_status['hp'] > 3: # If healthy, ensure it's not too low
            bid = max(bid, DAILY_SALARY * 0.65)
        else: # If low HP, even more critical
            bid = max(bid, DAILY_SALARY * 0.8)

    # 4. Survival Bid (Overwrites/Increases previous bid if necessary due to low HP)
    if my_status['hp'] <= 1:
        bid = min(my_status['budget'], DAILY_SALARY * 1.5) # Extremely aggressive, high priority
    elif my_status['hp'] <= 3:
        bid = max(bid, DAILY_SALARY * 0.95) # Aggressive bid if not already higher

    # 5. End Game Adjustment (Increases bid if necessary towards the end)
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days
        if my_status['hp'] <= 3:
            bid = max(bid, DAILY_SALARY * 0.98)
        else:
            bid = max(bid, DAILY_SALARY * 0.8) # Still competitive, as it's end game

    # Final check and cap by budget, ensure positive bid
    final_bid = max(1.0, min(my_status['budget'], bid))
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid conservatively
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid initialization
    my_bid = DAILY_SALARY * 0.6  # Default moderate bid

    # Adjust bid for survival (low HP or no water days)
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        my_bid = DAILY_SALARY * 0.95 # Aggressive for survival

    # Adjust bid based on opponent's previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if my_status['hp'] <= 3 or my_status['no_water_days'] > 0: # Still in survival mode, with opponent context
            # Bid high to ensure water, slightly above highest_prev_bid, capped by salary fraction
            my_bid = min(my_status['budget'], DAILY_SALARY * 0.95, highest_prev_bid + 5)
        else: # HP is good, no immediate water crisis
            if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents are bidding high
                # Slightly outbid them, but don't overcommit
                my_bid = min(my_status['budget'], highest_prev_bid * 1.05 + 1)
            else: # Opponents not bidding excessively high
                # Bid slightly above their max, but at least a moderate amount
                my_bid = min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 2))
    
    # Day-specific adjustments (End game pressure)
    current_day = day_context['day']
    remaining_days = EPISODE_DAYS - current_day

    if remaining_days <= 2: # Last 2 days
        if my_status['hp'] > 0: # If still in the game
            # Be more aggressive to secure win, cap at 120% salary
            my_bid = min(my_status['budget'], my_bid * 1.1 + 10, DAILY_SALARY * 1.2)
        else: # Already lost health, no point bidding
            my_bid = 0.0

    # Ensure bid is not negative and within budget
    return max(0.0, min(my_status['budget'], my_bid))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid low to save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Base bid starting point
    base_bid = DAILY_SALARY * 0.5

    # Analyze yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95 # Bid very aggressively
    elif my_status['hp'] <= 4: # Low HP
        base_bid = max(base_bid, DAILY_SALARY * 0.8) # Bid aggressively
    elif my_status['hp'] <= 6: # Medium HP
        base_bid = max(base_bid, DAILY_SALARY * 0.7)

    # Adjust bid based on previous opponent bids
    if max_yesterday_bid > 0:
        # Try to slightly outbid the highest opponent bid if it's competitive
        if max_yesterday_bid >= DAILY_SALARY * 0.6:
            base_bid = max(base_bid, max_yesterday_bid + 1.5) # Add a small buffer
        # If opponent bids are low, don't overbid too much, but still be competitive
        else:
            base_bid = max(base_bid, max_yesterday_bid * 1.1)

    # Adjust bid based on supply scarcity
    # Since WATER_REQ (13) + WATER_REQ (13) = 26, and MAX_SUPPLY is 25, 
    # it's always competitive for two agents needing full water.
    if day_context['supply'] <= 18: # Very low supply
        base_bid = max(base_bid, DAILY_SALARY * 0.75) # Increase bid for higher competition
    elif day_context['supply'] <= 21: # Medium supply
        base_bid = max(base_bid, DAILY_SALARY * 0.6)

    # Adjust bid based on day progress (end game pressure)
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days
        base_bid = max(base_bid, DAILY_SALARY * 0.9) # Be very aggressive to finish strong
    elif day_context['day'] >= EPISODE_DAYS / 2: # Second half of the game
        base_bid = max(base_bid, DAILY_SALARY * 0.7)

    # Ensure bid does not exceed budget and allows for profit (unless desperate)
    # If HP is critical, prioritize water over profit
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        final_bid = min(my_status['budget'], base_bid)
    else:
        final_bid = min(my_status['budget'], base_bid, DAILY_SALARY - 1) # Try to make at least 1 profit

    # Ensure a reasonable minimum bid to stay in contention
    final_bid = max(final_bid, DAILY_SALARY * 0.2)

    return round(final_bid, 2)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = 0.0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    bid = 0.0

    # Critical HP: Bid very high
    if my_status['hp'] <= 2:
        bid = DAILY_SALARY * 0.95
    # Low HP: Bid high
    elif my_status['hp'] <= 5:
        bid = DAILY_SALARY * 0.8
    # Healthy HP: Be more strategic
    else:
        # If max_yesterday_bid was high, be competitive
        if max_yesterday_bid >= DAILY_SALARY * 0.7:
            bid = max_yesterday_bid + 2.0
        # If max_yesterday_bid was moderate, bid slightly above average or a good base
        elif max_yesterday_bid >= DAILY_SALARY * 0.4:
            bid = max(DAILY_SALARY * 0.6, max_yesterday_bid + 1.5)
        # If max_yesterday_bid was low, try to win cheaply but don't risk it too much
        else:
            bid = DAILY_SALARY * 0.55

    # Adjust bid based on day progression (increase bids towards the end)
    day_multiplier = 1 + (day_context['day'] / EPISODE_DAYS) * 0.1
    bid *= day_multiplier

    # Adjust based on supply scarcity (low supply = more competition)
    supply_norm = (MAX_SUPPLY - day_context['supply']) / (MAX_SUPPLY - MIN_SUPPLY)
    bid += supply_norm * (DAILY_SALARY * 0.05)

    # Ensure bid is at least a reasonable amount to win
    bid = max(bid, DAILY_SALARY * 0.3)

    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], bid)
    
    # Ensure bid is non-negative
    final_bid = max(0.0, final_bid)

    return final_bid
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

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid_value = DAILY_SALARY * 0.5 # Default moderate bid

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP, need water desperately
        bid_value = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5: # Low HP, high urgency
        bid_value = DAILY_SALARY * 0.75
    else: # Healthy HP, can be more strategic
        bid_value = DAILY_SALARY * 0.55

    # Adjust based on yesterday's highest opponent bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were very aggressive yesterday, react strongly
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            bid_value = max(bid_value, highest_prev_bid + 5) # Try to outbid aggressive opponents
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            bid_value = max(bid_value, highest_prev_bid + 2) # Slightly above moderate bids
        else:
            bid_value = max(bid_value, highest_prev_bid + 1) # Just a little above low bids

    # Adjust bid based on the day (urgency increases towards the end)
    day_factor = 1 + (day_context['day'] / float(EPISODE_DAYS)) * 0.2
    bid_value *= day_factor

    # Ensure bid doesn't exceed budget and is at least 1
    final_bid = min(my_status['budget'], bid_value)
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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                yesterday_bids.append(prev_trace['bid'])

    base_bid = DAILY_SALARY * 0.5

    if my_hp <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4:
        base_bid = DAILY_SALARY * 0.75
    elif my_hp >= 8:
        base_bid = DAILY_SALARY * 0.4

    if current_day >= EPISODE_DAYS - 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    if current_supply < WATER_REQ + 5:
        base_bid = max(base_bid, DAILY_SALARY * 0.6)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid > DAILY_SALARY * 0.8:
            if my_hp <= 4 or current_supply < WATER_REQ + 5:
                base_bid = max(base_bid, highest_prev_bid + 5)
            else:
                base_bid = max(base_bid, DAILY_SALARY * 0.6)
        elif highest_prev_bid > DAILY_SALARY * 0.4:
            base_bid = max(base_bid, highest_prev_bid + 2)

    final_bid = min(my_budget, base_bid)

    if final_bid == 0 and my_budget > 0:
        return min(my_budget, 1)
    elif final_bid == 0 and my_budget == 0:
        return 0

    return final_bid
"""
