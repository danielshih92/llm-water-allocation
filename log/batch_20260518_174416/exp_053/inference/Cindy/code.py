# ============================================================
# Experiment: exp_053
# Agent: Cindy
# Source: exp_053
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQ = 13
    MY_DAILY_SALARY = 150

    # Define bid thresholds based on MY_DAILY_SALARY, mirroring the example's logic
    MY_BID_IF_HP_GOOD_OPP_HIGH = MY_DAILY_SALARY * 0.3
    MY_BID_IF_HP_BAD_OPP_HIGH = MY_DAILY_SALARY * 0.95
    MY_BID_FLOOR_MODERATE_OPP = MY_DAILY_SALARY * 0.5
    MY_BID_IF_NO_PREV_HP_BAD = MY_DAILY_SALARY * 0.9
    MY_BID_IF_NO_PREV_HP_GOOD = MY_DAILY_SALARY * 0.55

    # Threshold for interpreting opponent's previous bid as 'high pressure'
    OPPONENT_HIGH_BID_THRESHOLD = MY_DAILY_SALARY * 0.85

    BID_INCREMENT = 1.5 # Increment to bid above opponent's previous bid, as in example

    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to save budget
    if num_alive_opponents == 0:
        return min(my_budget, MY_DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    final_bid = 0.0 # Initialize final_bid as float

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # Directly apply the logic from the example's game theory
        if highest_prev_bid >= OPPONENT_HIGH_BID_THRESHOLD:
            # Opponents showed high pressure (bid aggressively yesterday)
            if my_hp > 3: # My HP is good, can afford to let them overspend
                final_bid = MY_BID_IF_HP_GOOD_OPP_HIGH
            else: # My HP is bad, must compete aggressively
                final_bid = MY_BID_IF_HP_BAD_OPP_HIGH
        else:
            # Opponents did not show extremely high pressure yesterday
            # Bid slightly above their highest previous bid, with a floor
            final_bid = max(MY_BID_FLOOR_MODERATE_OPP, highest_prev_bid + BID_INCREMENT)
    else:
        # No previous bids (e.g., first day of the meta-round or opponents are new)
        # Fallback to HP-based bidding, similar to example's 'no yesterday_bids' case
        if my_hp <= 2: # My HP is critical
            final_bid = MY_BID_IF_NO_PREV_HP_BAD
        else: # My HP is good enough
            final_bid = MY_BID_IF_NO_PREV_HP_GOOD

    # Ensure the bid is within budget and is at least 1.0
    final_bid = min(my_budget, max(1.0, final_bid))

    # Critical rule: if HP is 1, bid everything to survive
    if my_hp == 1:
        final_bid = my_budget

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

    # Default bid: a moderate percentage of daily salary
    bid = DAILY_SALARY * 0.50 # 75

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # **Strategy Adjustments**

    # 1. High urgency: Low HP or consecutive no-water days
    if my_status['hp'] <= 3 or my_status['no_water_days'] > 0:
        bid = DAILY_SALARY * 0.95 # 142.5 - Critical survival bid

    # 2. Late game urgency: Days 8, 9, 10
    elif day_context['day'] >= EPISODE_DAYS - 2: # Last 3 days
        bid = max(bid, DAILY_SALARY * 0.85) # 127.5 - Secure water towards the end

    # 3. React to opponent's previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were very aggressive, try to outbid them
        if highest_prev_bid >= DAILY_SALARY * 0.75:
            bid = max(bid, highest_prev_bid + 5)
        # If opponents were moderately aggressive, slightly increase bid to stay competitive
        elif highest_prev_bid > DAILY_SALARY * 0.4:
            bid = max(bid, highest_prev_bid + 1)

    # 4. Adjust for supply scarcity
    # If supply is tight (less than enough for 2 players' full requirement), bid higher
    if day_context['supply'] < WATER_REQ * 2:
        bid = max(bid, DAILY_SALARY * 0.8)

    # Ensure bid does not exceed current budget
    return min(my_status['budget'], bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    yesterday_bids = []
    opponents_lost_hp_yesterday = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            if prev.get('status') != 'SURVIVED':
                opponents_lost_hp_yesterday += 1

    max_yesterday_opp_bid = 0
    if yesterday_bids:
        max_yesterday_opp_bid = max(yesterday_bids)

    base_bid = DAILY_SALARY * 0.5
    bid = base_bid

    # Adjust bid based on my HP and no_water_days
    if my_hp <= 2 or my_no_water_days >= 1: # Critical HP or already losing HP
        bid = DAILY_SALARY * 0.95
        if max_yesterday_opp_bid > bid:
             bid = max(bid, max_yesterday_opp_bid * 1.05)
    elif my_hp <= 5: # Low HP
        bid = DAILY_SALARY * 0.75
        if max_yesterday_opp_bid > bid:
            bid = max(bid, max_yesterday_opp_bid * 1.02)
    else: # Healthy HP
        # Adjust based on number of opponents and their desperation
        if num_alive_opponents == 0:
            bid = DAILY_SALARY * 0.1 # No competition, bid minimal
        elif opponents_lost_hp_yesterday >= num_alive_opponents / 2: # Many opponents are desperate
            bid = max(bid, DAILY_SALARY * 0.6)
            if max_yesterday_opp_bid > bid:
                bid = max(bid, max_yesterday_opp_bid * 1.01)
        else: # Fewer desperate opponents, or generally lower bids
            if max_yesterday_opp_bid > base_bid:
                bid = max(bid, max_yesterday_opp_bid * 0.98)

    # Adjust bid based on supply (lower supply = higher competition = higher bid)
    supply_pressure = (MAX_SUPPLY - current_supply) / (MAX_SUPPLY - MIN_SUPPLY)
    bid *= (1 + supply_pressure * 0.2)

    # Adjust for end game (last few days)
    if current_day >= EPISODE_DAYS - 2:
        if my_hp < 10 or my_no_water_days >= 1:
            bid *= 1.15
        else:
            bid *= 1.05

    bid = max(bid, DAILY_SALARY * 0.15)
    bid = min(bid, my_budget)

    return round(bid, 2)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents are alive, bid minimally to save budget.
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Analyze yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # 1. Critical HP: If HP is very low, bid aggressively to survive.
    if my_hp <= 2:
        return min(my_budget, DAILY_SALARY * 1.25)

    # 2. End Game Strategy: If close to the end, and doing well, try to secure win.
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2:
        if my_hp >= 5 and my_budget > DAILY_SALARY * 2:
            return min(my_budget, DAILY_SALARY * 1.1)
        else:
            return min(my_budget, DAILY_SALARY * 1.2)

    # 3. Adapt to opponent's previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.9: # Opponents are bidding aggressively
            # If supply is tight, competition is higher.
            # Check if supply is less than what all alive opponents (including self) would need if they all got their requirement
            if current_supply <= WATER_REQ * (num_alive_opponents + 1): # +1 for myself
                return min(my_budget, max(DAILY_SALARY * 1.05, highest_prev_bid + 5))
            else:
                return min(my_budget, max(DAILY_SALARY * 0.95, highest_prev_bid * 1.02))
        else: # Opponents are bidding relatively low or moderate
            return min(my_budget, max(DAILY_SALARY * 0.8, highest_prev_bid + 2))
    else: # 4. Default / No previous bids available (e.g., Day 1 or all opponents died yesterday)
        # Adjust based on supply and number of opponents
        if num_alive_opponents >= 3: # High competition
            if current_supply <= WATER_REQ * (num_alive_opponents + 1): # Tight supply
                return min(my_budget, DAILY_SALARY * 1.05)
            else:
                return min(my_budget, DAILY_SALARY * 0.9)
        else: # Moderate competition (1 or 2 opponents)
            if current_supply <= WATER_REQ * (num_alive_opponents + 1): # Tight supply
                return min(my_budget, DAILY_SALARY * 0.95)
            else:
                return min(my_budget, DAILY_SALARY * 0.8)

    # Fallback bid (should ideally not be reached if logic is exhaustive)
    return min(my_budget, DAILY_SALARY * 0.9)
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

    alive_opponents = [o for o_id, o in opponents_status.items() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.3)

    base_bid = DAILY_SALARY * 0.7

    if my_hp <= 2:
        base_bid = DAILY_SALARY * 0.99
    elif my_hp <= 4:
        base_bid = DAILY_SALARY * 0.9
    elif my_no_water_days >= 1:
        base_bid = DAILY_SALARY * 0.85

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            if my_hp <= 3:
                base_bid = max(base_bid, highest_prev_bid + 2.5)
            else:
                base_bid = max(base_bid, highest_prev_bid * 1.01)
        elif highest_prev_bid >= DAILY_SALARY * 0.7:
            base_bid = max(base_bid, highest_prev_bid + 1.5)
        else:
            base_bid = max(base_bid, highest_prev_bid + 1)

    days_left = EPISODE_DAYS - current_day
    if days_left <= 2:
        if my_hp > 0:
            base_bid = max(base_bid, DAILY_SALARY * 1.0)
            if my_hp <= 1:
                base_bid = max(base_bid, my_budget)
    elif days_left <= 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)

    final_bid = min(my_budget, base_bid)

    if final_bid <= 0 and my_budget > 0:
        final_bid = 1.0

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
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_agents = len(alive_opponents) + 1 # Including myself

    # If no opponents, bid low to save money
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

    # Determine base bid
    bid = DAILY_SALARY * 0.6 # Default moderate bid

    # Adjust based on my HP
    if my_status['hp'] <= 2: # Critical HP
        bid = DAILY_SALARY * 0.98
    elif my_status['hp'] <= 4: # Low HP
        bid = DAILY_SALARY * 0.85
    else: # Good HP
        # Adjust based on supply scarcity
        # If supply is less than enough for 2 agents, it's very competitive
        if day_context['supply'] < 2 * WATER_REQ:
            bid = DAILY_SALARY * 0.75
        elif day_context['supply'] < 3 * WATER_REQ:
            bid = DAILY_SALARY * 0.65
        else: # More abundant supply
            bid = DAILY_SALARY * 0.55

    # Adjust based on highest previous bid (exploiting opponent's past behavior)
    if highest_prev_bid > 0:
        # If opponents bid very high, and I need water, I must compete
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Alex/Eric territory
            if my_status['hp'] <= 4 or day_context['day'] >= EPISODE_DAYS * 0.7: # Need water or late game
                bid = max(bid, highest_prev_bid + 5) # Try to outbid
            else: # Good HP, early/mid game, let them overspend if possible
                bid = min(bid, highest_prev_bid * 0.95) # Bid slightly below or similar, but don't overcommit
                bid = max(bid, DAILY_SALARY * 0.6) # Ensure a reasonable floor
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderate bids (could be David/Bob or slightly lower Alex/Eric)
            bid = max(bid, highest_prev_bid + 2) # Slightly outbid
        else: # Low bids (Bob/David territory)
            bid = max(bid, highest_prev_bid + 10) # Ensure I win against low bidders, but still conservative
            bid = min(bid, DAILY_SALARY * 0.6) # Don't overpay if competition is weak

    # Ensure bid doesn't exceed budget and is not negative
    final_bid = min(my_status['budget'], max(0.0, bid))

    # Ensure a minimal bid if not dead and have budget, to stay in game
    # my_status['hp'] > -EPISODE_DAYS is a proxy for not being 'dead' or about to die from negative HP
    if my_status['hp'] > -EPISODE_DAYS and final_bid < DAILY_SALARY * 0.1 and my_status['budget'] > 0:
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10

    current_day = day_context['day']
    current_supply = day_context['supply']

    # Base bid calculation
    # Start with a moderate bid, aiming to secure water without overspending too early.
    bid = DAILY_SALARY * 0.5 # Default to 50% of daily salary

    # Adjust bid based on my current HP (survival priority)
    if my_status['hp'] <= 2: # Critical HP, bid aggressively
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP, bid high
        bid = DAILY_SALARY * 0.75
    elif my_status['hp'] >= 8 and my_status['budget'] > DAILY_SALARY * 2: # Healthy and good budget, can be a bit conservative
        bid = DAILY_SALARY * 0.4

    # Adjust bid based on supply scarcity
    # If supply is very tight, competition will be higher
    if current_supply <= WATER_REQ + 3: # E.g., supply 15-16, only enough for one agent's full requirement
        bid *= 1.15 # Increase bid significantly
    elif current_supply >= MAX_SUPPLY - 5: # E.g., supply 20-25, relatively abundant water
        bid *= 0.85 # Decrease bid

    # Opponent analysis from yesterday's trace
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    opponent_yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            opponent_yesterday_bids.append(prev['bid'])

    if opponent_yesterday_bids:
        max_opp_bid_yesterday = max(opponent_yesterday_bids)

        # If top opponent bid was very high yesterday, we might need to outbid or match
        if max_opp_bid_yesterday > DAILY_SALARY * 0.7: # If an opponent bid very high
            bid = max(bid, max_opp_bid_yesterday + 5) # Try to slightly outbid them
        # If top opponent bid was low and my HP is good, we might be able to save money
        elif max_opp_bid_yesterday < DAILY_SALARY * 0.4 and my_status['hp'] > 5:
            bid = min(bid, DAILY_SALARY * 0.4) # Don't go too low, but conserve

    # Ensure bid is not too low to be competitive, especially if supply is tight
    min_competitive_bid = DAILY_SALARY * 0.3 # Base minimum bid
    if current_supply <= WATER_REQ * 1.5: # If supply is somewhat limited
        min_competitive_bid = DAILY_SALARY * 0.35
    bid = max(bid, min_competitive_bid)

    # Final adjustments
    # Ensure bid does not exceed available budget
    final_bid = min(my_status['budget'], bid)

    # Ensure bid is not negative
    final_bid = max(0.0, final_bid)

    # On the last day, if water is needed, bid very high to win
    if current_day == EPISODE_DAYS and my_status['hp'] < EPISODE_DAYS: # If not already guaranteed survival
         final_bid = min(my_status['budget'], DAILY_SALARY * 1.5) # Bid very high to secure water

    # If I have a lot of budget and it's early, be more aggressive to establish dominance
    # Check if budget is significantly more than what's needed for future salaries
    if current_day < EPISODE_DAYS / 2 and my_status['budget'] > DAILY_SALARY * (EPISODE_DAYS - current_day) * 1.2:
        final_bid = max(final_bid, DAILY_SALARY * 0.6) # Ensure a strong bid early on if flush with cash

    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # 1. Immediate exit: If no opponents, bid minimally to save budget.
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # 2. Base Bid Calculation - starts with a default and gets adjusted
    bid = DAILY_SALARY * 0.5

    # 3. Adjust bid based on my status (HP, no_water_days)
    if my_status['no_water_days'] >= 1: # Desperate: missed water yesterday
        bid = DAILY_SALARY * 0.98
    elif my_status['hp'] <= 2: # Critically low HP
        bid = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 4: # Low HP
        bid = DAILY_SALARY * 0.75
    else: # Healthy HP, can be more conservative
        bid = DAILY_SALARY * 0.55

    # 4. Adjust bid based on supply context
    # Supply pressure is higher when supply is low.
    # supply_pressure ranges from 1.0 (min supply) to 0.0 (max supply).
    supply_pressure = 1.0 - ((day_context['supply'] - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))
    # Apply a multiplier: higher pressure means higher bid. Multiplier from 1.0 to 1.3
    bid *= (1.0 + supply_pressure * 0.3)

    # 5. Analyze opponent's previous bids from yesterday's trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        # Only consider valid bids from previous day
        if prev and prev.get('bid') is not None and prev.get('status') != 'error':
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # React to opponent's aggression from yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents were very aggressive
            if my_status['hp'] <= 3: # My HP is low, must secure water
                bid = max(bid, highest_prev_bid * 1.05)
            else: # My HP is healthy, try to be competitive but not overspend
                bid = max(bid, highest_prev_bid * 0.9)
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderately aggressive
            bid = max(bid, average_prev_bid * 1.02)
        else: # Opponents were conservative
            # Try to win but save budget, bid slightly above their average if my current bid isn't already high enough
            bid = max(bid, average_prev_bid * 1.1)
    # Else: no yesterday_bids, 'bid' remains as adjusted by my status and supply.

    # 6. Final bid adjustments and constraints
    # Ensure bid is always positive and within budget
    final_bid = min(my_status['budget'], bid)
    final_bid = max(0.0, final_bid)

    # Survival override: If critically low HP or consecutive no-water days, bid almost all budget
    if my_status['hp'] <= 1 and my_status['budget'] > 0:
        final_bid = my_status['budget'] * 0.99
    elif my_status['no_water_days'] >= 2 and my_status['budget'] > 0:
        final_bid = my_status['budget'] * 0.99
    # If budget is low and I still need water, bid a significant portion
    elif my_status['budget'] < DAILY_SALARY * 0.6 and my_status['hp'] <= 3 and my_status['budget'] > 0:
        final_bid = max(final_bid, my_status['budget'] * 0.9) # Ensure a strong bid with limited budget

    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no alive opponents, bid minimally to secure water cheaply
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    # Collect yesterday's bids from all alive opponents
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Decision logic based on yesterday's highest pressure and current HP
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If previous bids were very high, indicating fierce competition
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # Not critical, try to save budget
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            else: # Critical HP, bid aggressively
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else: # Previous bids were moderate, react slightly above them
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
    
    # If no previous bids (e.g., first day of meta-round or opponents are new/no trace)
    if my_status['hp'] <= 2: # Critical HP, bid high
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    else: # Not critical, bid moderately
        return min(my_status['budget'], DAILY_SALARY * 0.55)
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('day') == current_day - 1 and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    base_bid = DAILY_SALARY * 0.85

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            if my_hp <= 3 or my_no_water_days >= 1:
                base_bid = highest_prev_bid + 5
            else:
                base_bid = max(base_bid, highest_prev_bid + 1)
        else:
            if my_hp <= 3 or my_no_water_days >= 1:
                base_bid = max(base_bid, highest_prev_bid + 10)
            else:
                base_bid = max(base_bid, DAILY_SALARY * 0.75)
    
    if my_hp <= 1:
        base_bid = my_budget
    elif my_hp <= 3 or my_no_water_days >= 1:
        base_bid = max(base_bid, DAILY_SALARY * 0.95)

    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 1 and my_hp <= 5:
        base_bid = my_budget
    elif remaining_days <= 2 and my_hp <= 3:
        base_bid = max(base_bid, my_budget * 0.8)

    final_bid = min(my_budget, base_bid)

    return max(1.0, final_bid)
"""
