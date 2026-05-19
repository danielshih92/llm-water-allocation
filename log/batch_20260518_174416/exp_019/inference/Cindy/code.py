# ============================================================
# Experiment: exp_019
# Agent: Cindy
# Source: exp_019
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    TOTAL_DAYS = 10 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    current_day = day_context['day']
    
    # --- Stage 1: Critical Survival --- 
    # If HP is 1 or 2, I need water desperately. Bid very high.
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # --- Stage 2: No Competition --- 
    # No opponents, bid minimum to get water and save budget.
    if num_alive_opponents == 0:
        return min(my_status['budget'], WATER_REQ * 1.1)

    # --- Stage 3: General Bidding Strategy --- 
    yesterday_bids = []
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid strategy based on my HP
    my_target_bid = 0
    if my_status['hp'] == 3:
        my_target_bid = DAILY_SALARY * 0.75 # Aggressive if HP is 3
    elif my_status['hp'] == 4:
        my_target_bid = DAILY_SALARY * 0.65 # Moderately aggressive if HP is 4
    else: # my_status['hp'] >= 5 (good HP)
        my_target_bid = DAILY_SALARY * 0.55 # Conservative if HP is good

    # Adjust target bid based on opponent's previous highest bid
    # Water supply (15-25) vs my WATER_REQ (13) means usually only one agent can get full water.
    # Thus, competition is always high for the main water slot.
    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.8 and my_status['hp'] > 4 and my_status['budget'] > DAILY_SALARY * 2:
            # If opponent is super aggressive, my HP is good, and I have budget cushion,
            # I can afford to let them win one if they overbid, and conserve my budget.
            my_target_bid = min(my_target_bid, highest_prev_bid * 0.9) # Try to save, but still in the game
        else:
            # Otherwise, or if I need water more, try to outbid them.
            my_target_bid = max(my_target_bid, highest_prev_bid + 1)

    # Adjust if I've been losing water recently (no_water_days)
    if my_status['no_water_days'] > 0:
        my_target_bid = my_target_bid * (1 + my_status['no_water_days'] * 0.07) # Increase bid more aggressively

    # Adjust for end game: Be more aggressive if few days left and I have budget
    remaining_days = TOTAL_DAYS - current_day
    if remaining_days <= 2: # Last 2 days
        if my_status['hp'] > 2 and my_status['budget'] > DAILY_SALARY * 1.5:
            my_target_bid = max(my_target_bid, DAILY_SALARY * 0.85) # Push for wins
        else: # Not critical, but still need to secure water in the end game
            my_target_bid = max(my_target_bid, DAILY_SALARY * 0.75)

    # Ensure a minimum bid to be competitive and show intent
    # Given water scarcity, a bid below 40% of salary is likely too low to win.
    min_competitive_bid = DAILY_SALARY * 0.4
    my_target_bid = max(my_target_bid, min_competitive_bid)

    # Final bid must be within budget
    final_bid = min(my_status['budget'], my_target_bid)
    
    # Ensure final_bid is not zero if budget allows, or if it falls below water cost.
    # The actual cost is 2nd highest, but I need to bid high enough to win.
    if final_bid < WATER_REQ * 1.1:
        final_bid = min(my_status['budget'], WATER_REQ * 1.1)

    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents are alive, bid a minimal amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Determine my current need for water
    # Level 2: Critical - missed water yesterday
    # Level 1: High - low HP
    # Level 0: Normal - good HP and not missed water
    my_need_level = 0
    if my_status['no_water_days'] > 0:
        my_need_level = 2 
    elif my_status['hp'] <= 2:
        my_need_level = 1 
    
    # Analyze yesterday's bids from currently alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Initialize my bid
    my_bid = 0.0

    # Bidding logic based on need level and opponent behavior
    if my_need_level == 2: # Critical need: must get water
        # Bid very aggressively, potentially close to or slightly above daily salary
        my_bid = max(highest_prev_bid + 5.0, DAILY_SALARY * 0.98)
    
    elif my_need_level == 1: # High need: HP is low
        # Bid high to secure water, but slightly less aggressive than critical
        my_bid = max(highest_prev_bid + 3.0, DAILY_SALARY * 0.90)

    else: # Normal state: good HP, haven't missed water
        # Aim to win by slightly exceeding yesterday's highest bid, conserving budget
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents are bidding relatively high
            my_bid = max(highest_prev_bid + 2.0, DAILY_SALARY * 0.85)
        else: # Opponents are bidding lower, or no strong bids yesterday
            my_bid = max(highest_prev_bid + 1.0, DAILY_SALARY * 0.75)
            
    # Ensure bid does not exceed available budget
    return min(my_status['budget'], my_bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are left, bid a minimal amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # If I'm in critical HP, bid aggressively to survive
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 1.1) # Bid slightly above salary

    # If I'm in moderate HP, still need to be competitive
    if my_status['hp'] == 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # If I have healthy HP, I can be more strategic
    if my_status['hp'] >= 4:
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)

            # If opponents were bidding very high, try to match/exceed slightly
            if highest_prev_bid >= DAILY_SALARY * 0.9:
                return min(my_status['budget'], highest_prev_bid * 1.05)
            # If opponents were bidding moderately, bid slightly above their highest
            elif highest_prev_bid >= DAILY_SALARY * 0.6:
                return min(my_status['budget'], highest_prev_bid + 10)
            # If opponents were bidding low, bid a bit higher than them but not excessively
            else:
                return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 5))

        # If no yesterday bids (e.g., Day 1 or opponents were inactive)
        # Default bid for healthy HP
        return min(my_status['budget'], DAILY_SALARY * 0.7)

    # Fallback bid (should not be reached with the current logic)
    return min(my_status['budget'], DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQUIREMENT = 13
    MY_DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to secure water and save budget.
    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    yesterday_bids = []
    total_water_needed_by_alive_agents = MY_WATER_REQUIREMENT # My requirement

    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            total_water_needed_by_alive_agents += opp_data['water_requirement']
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

    # Determine a base bid based on my status and general market conditions
    base_bid = MY_DAILY_SALARY * 0.55 # Start with 55% of salary

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP, must get water
        base_bid = MY_DAILY_SALARY * 0.95 # Very aggressive bid
    elif my_status['hp'] <= 4: # Low HP, prioritize water
        base_bid = MY_DAILY_SALARY * 0.8 # Moderately aggressive

    # Adjust bid based on supply scarcity
    # If supply is less than total water needed, competition is high
    if day_context['supply'] < total_water_needed_by_alive_agents:
        if my_status['hp'] > 4: # If healthy, increase bid slightly in scarce conditions
            base_bid = max(base_bid, MY_DAILY_SALARY * 0.7)
        elif my_status['hp'] > 2: # If low but not critical, increase more
            base_bid = max(base_bid, MY_DAILY_SALARY * 0.85)
    else: # Supply is abundant or sufficient
        if my_status['hp'] > 4: # If healthy, try to save money
            base_bid = min(base_bid, MY_DAILY_SALARY * 0.4)

    # Adjust based on yesterday's highest bid from active opponents
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were very aggressive yesterday
        if highest_prev_bid >= MY_DAILY_SALARY * 0.8:
            if my_status['hp'] <= 3: # If critical HP, outbid them
                base_bid = max(base_bid, highest_prev_bid + 5)
            elif my_status['hp'] <= 5: # If low HP, match or slightly exceed
                base_bid = max(base_bid, highest_prev_bid + 1)
            else: # If healthy, don't get into a bidding war unless supply is very low
                if day_context['supply'] < total_water_needed_by_alive_agents:
                    base_bid = max(base_bid, highest_prev_bid)
                else:
                    base_bid = min(base_bid, MY_DAILY_SALARY * 0.7) # Try to save

        # If opponents were moderately aggressive
        elif highest_prev_bid >= MY_DAILY_SALARY * 0.5:
            if my_status['hp'] <= 4:
                base_bid = max(base_bid, highest_prev_bid + 1)
            else:
                base_bid = max(base_bid, MY_DAILY_SALARY * 0.55) # Maintain a good bid

        # If opponents were conservative
        else:
            if my_status['hp'] > 4 and day_context['supply'] > total_water_needed_by_alive_agents:
                base_bid = min(base_bid, MY_DAILY_SALARY * 0.35) # Try to save even more
            else:
                base_bid = max(base_bid, highest_prev_bid + 1) # Still ensure I win if I need water

    # Ensure bid is within budget and non-negative
    final_bid = min(my_status['budget'], max(0.0, base_bid))

    # Smallest possible bid to ensure participation if budget is very low but not 0
    if final_bid == 0.0 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], 0.1)
    elif final_bid == 0.0 and my_status['budget'] == 0:
        return 0.0 # Cannot bid if budget is 0

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
    num_opponents = len(alive_opponents)
    
    if num_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Desperation mode: If HP is critically low, bid very aggressively
    # hp=1 means 1 day left, hp=2 means 2 days left
    if my_status['hp'] <= 2:
        # The multiplier increases as hp decreases, ensuring higher bids closer to death
        desperation_multiplier = 0.95 + (0.1 * (3 - my_status['hp'])) # 1.05 for hp=2, 1.15 for hp=1
        bid = DAILY_SALARY * desperation_multiplier
        return min(my_status['budget'], bid)
    
    # Normal bidding strategy
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    base_bid = DAILY_SALARY * 0.65 # A strong starting point given high competition

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        
        # Adjust bid based on max previous bid to slightly outbid competitors
        if max_yesterday_bid >= DAILY_SALARY * 0.85: # Opponents are very aggressive
            bid = max_yesterday_bid + 5 
        elif max_yesterday_bid >= DAILY_SALARY * 0.7: # Opponents are aggressive
            bid = max_yesterday_bid + 3
        else: # Opponents are moderate or low
            bid = max(base_bid, max_yesterday_bid + 1) # Ensure we don't bid too low
    else:
        # No previous bids (e.g., Day 1 or all opponents failed to bid yesterday)
        # Bid aggressively on Day 1 due to the inherently high competition for water
        if day_context['day'] == 1 and num_opponents > 0:
            bid = DAILY_SALARY * 0.75
        else:
            bid = base_bid

    # Cap the bid to prevent overspending when not desperate
    # Allow bidding slightly above salary if competition demands, but not excessively
    if my_status['hp'] > 2: # Not desperate
        bid = min(bid, DAILY_SALARY * 1.05) # Cap at 105% of daily salary
    
    final_bid = min(my_status['budget'], bid)
    
    # Ensure bid is at least a minimal value to participate meaningfully
    final_bid = max(final_bid, 0.01)

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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    supply = day_context['supply']

    # --- 1. Determine base bid based on my needs and game state --- 
    base_bid = DAILY_SALARY * 0.85 # Start with a conservative bid

    # Prioritize survival if HP is low
    if my_hp <= 2:
        base_bid = DAILY_SALARY * 1.15
    elif my_hp <= 4:
        base_bid = DAILY_SALARY * 1.05

    # Increase bid towards end of the episode
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        base_bid = max(base_bid, DAILY_SALARY * 1.2)
    elif current_day >= EPISODE_DAYS - 4: # Last 4 days
        base_bid = max(base_bid, DAILY_SALARY * 1.1)

    # Adjust for supply scarcity
    # If supply is less than or equal to my requirement, competition is very high for just one slot
    if supply <= WATER_REQ:
        base_bid = max(base_bid, DAILY_SALARY * 1.1) # Bid very aggressively if supply is scarce
    # If supply is enough for two people (2 * WATER_REQ = 26), but less than 26, it's still tight
    elif supply <= (2 * WATER_REQ):
        base_bid = max(base_bid, DAILY_SALARY * 1.0) # Ensure it's at least salary if supply is tight

    # --- 2. React to opponents' previous bids --- 
    eric_prev_bid = 0.0
    eric_current_budget = 0.0
    bob_prev_bid = 0.0
    bob_current_budget = 0.0
    highest_prev_bid_among_active = 0.0

    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            current_opp_budget = opp_data['budget'] # This is their budget at the start of THIS day (includes today's salary)
            prev_trace = opp_data.get('previous_trace', {})
            prev_bid = prev_trace.get('bid', 0.0) if prev_trace else 0.0

            if prev_bid is not None:
                highest_prev_bid_among_active = max(highest_prev_bid_among_active, prev_bid)

            if opp_id == "Eric":
                eric_prev_bid = prev_bid
                eric_current_budget = current_opp_budget
            elif opp_id == "Bob":
                bob_prev_bid = prev_bid
                bob_current_budget = current_opp_budget

    # If Eric was aggressive yesterday and has a *relatively* low budget today, try to outbid him.
    # Eric's budget for today (current_opp_budget) is his budget_after_yesterday + his_daily_salary.
    # Given Eric's final_budget (from LATEST METAROUND CONTEXT) was 107.0, and assuming his daily_salary is 150,
    # his budget today would be ~257. This is lower than Bob's, making him vulnerable to budget draining.
    if eric_prev_bid > DAILY_SALARY * 0.9 and eric_current_budget < (DAILY_SALARY * 2.0): # Eric bid high and his total budget for today is not huge
        # Try to outbid him slightly, but not excessively
        base_bid = max(base_bid, eric_prev_bid + 5.0)
        # Cap this aggressive bid to prevent overspending too much
        base_bid = min(base_bid, DAILY_SALARY * 1.25)

    # If Bob was aggressive, he has a large budget, so we might need to match or slightly exceed.
    if bob_prev_bid > DAILY_SALARY * 0.9:
        base_bid = max(base_bid, bob_prev_bid + 2.0)
        base_bid = min(base_bid, DAILY_SALARY * 1.2) # Cap it

    # General reaction to any high previous bid from an active opponent
    if highest_prev_bid_among_active > DAILY_SALARY * 1.0:
        base_bid = max(base_bid, highest_prev_bid_among_active + 1.0)
        base_bid = min(base_bid, DAILY_SALARY * 1.3)

    # --- 3. Final checks --- 
    # Ensure bid is always positive and not more than my current budget
    final_bid = max(0.1, base_bid)
    final_bid = min(final_bid, my_budget)

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
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    base_bid = DAILY_SALARY * 0.5

    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] >= 8:
        base_bid = DAILY_SALARY * 0.4
    
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] < 5:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif remaining_days <= 3 and my_status['hp'] >= 5:
        base_bid = max(base_bid, DAILY_SALARY * 0.6)

    current_supply = day_context['supply']
    total_water_demand_estimate = WATER_REQ
    for opp in alive_opponents:
        total_water_demand_estimate += opp['water_requirement']

    if current_supply < total_water_demand_estimate:
        base_bid *= 1.2
    elif current_supply >= total_water_demand_estimate * 1.5:
        base_bid *= 0.8

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        lowest_prev_bid = min(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] <= 5:
                base_bid = max(base_bid, highest_prev_bid + 5)
            else:
                base_bid = min(base_bid, highest_prev_bid * 0.7)
        elif highest_prev_bid > base_bid * 1.1:
             base_bid = max(base_bid, highest_prev_bid + 2)
        elif lowest_prev_bid < base_bid * 0.7 and my_status['hp'] > 5:
            base_bid = min(base_bid, lowest_prev_bid + 1)

    final_bid = min(my_status['budget'], max(1.0, base_bid))

    for opp_id, opp_data in opponents_status.items():
        if opp_id == "Bob" and opp_data['alive']:
            bob_prev_trace = opp_data.get('previous_trace', {})
            if bob_prev_trace and bob_prev_trace.get('bid') is not None:
                if bob_prev_trace['bid'] >= DAILY_SALARY * 0.7:
                    final_bid = max(final_bid, DAILY_SALARY * 0.75)

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

    # Initial bid based on my health
    if my_status['hp'] <= WATER_REQ * 0.5 or my_status['no_water_days'] > 0:
        # Critical health (HP <= 6.5) or no water yesterday, bid very aggressively
        my_bid = DAILY_SALARY * 0.98
    elif my_status['hp'] <= WATER_REQ * 1.0: # HP <= 13 (initial HP is 10, so this is true on Day 1)
        # Low health, bid aggressively
        my_bid = DAILY_SALARY * 0.85
    else:
        # Healthy, start with a moderate bid
        my_bid = DAILY_SALARY * 0.65

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid a minimal amount to get water
    if not alive_opponents:
        return min(my_status['budget'], WATER_REQ * 2.5)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Adjust bid based on opponent's previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were bidding very high yesterday (e.g., >=90% of a salary)
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            # If I'm very healthy AND have significant budget, I can consider letting them overbid
            if my_status['hp'] > WATER_REQ * 1.5 and my_status['budget'] > DAILY_SALARY * 3: # HP > 19.5 and Budget > 450
                # Bid lower than highest_prev_bid, but ensure it's not too low to be competitive if others drop
                my_bid = min(my_bid, highest_prev_bid * 0.75) # Try to conserve
                my_bid = max(my_bid, DAILY_SALARY * 0.55) # Ensure it's not too ridiculously low
            else: # Not healthy/rich enough to risk, must compete
                my_bid = max(my_bid, highest_prev_bid + 5.0) # Outbid them to secure water
        # If opponents were bidding high (e.g., >=70% of a salary)
        elif highest_prev_bid >= DAILY_SALARY * 0.7:
            my_bid = max(my_bid, highest_prev_bid + 3.0) # Stay competitive
        else: # Moderate pressure
            my_bid = max(my_bid, highest_prev_bid + 1.0) # Slightly outbid

    # Adjust for supply scarcity
    # Use int() for index as per CRITICAL INDEX RULE
    num_possible_winners = int(day_context['supply'] // WATER_REQ)
    # If not enough water for everyone (including myself)
    if num_possible_winners < len(alive_opponents) + 1:
        if my_status['hp'] <= WATER_REQ * 1.0: # If my HP is low (13 or less)
            my_bid = max(my_bid, DAILY_SALARY * 0.95) # Bid very aggressively
        else: # If healthy, still competitive but less desperate
            my_bid = max(my_bid, DAILY_SALARY * 0.8) # High bid

    # Ensure bid does not exceed my budget
    final_bid = min(my_status['budget'], my_bid)
    
    # Ensure bid is at least 0
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    # Since supply // WATER_REQ is always 1 (as supply is [15, 25] and WATER_REQ is 13),
    # only one agent can fulfill their full water requirement each day.
    # My initial HP is 10, and missing 13 water units means losing 13 HP, thus dying.
    # Therefore, I MUST win the bid for 13 units of water every single day to survive.

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid: a strong starting point, assuming competition.
    # It must be high enough to be competitive against opponents who bid above their salary.
    # Alex's max bid was 194.4, David's was 177.0. My salary is 150.
    strong_default_bid = DAILY_SALARY * 1.05 # 157.5

    my_bid = 0.0
    increment = 2.0 # A small amount to outbid

    # Strategy: Always aim to outbid the highest previous opponent bid.
    # Adjust aggressiveness based on day and budget.
    
    # If no previous bids from opponents or they were very low, use a strong default.
    if highest_prev_bid < strong_default_bid:
        my_bid = strong_default_bid
    else:
        my_bid = highest_prev_bid + increment

    # Adjust aggressiveness for later days if budget allows
    if day_context['day'] >= EPISODE_DAYS / 2: # Second half of the game
        # If I have a good budget, be more aggressive to try and eliminate opponents
        # Check if budget is sufficient for remaining days + a buffer
        if my_status['budget'] > (EPISODE_DAYS - day_context['day'] + 1) * DAILY_SALARY * 1.5: 
            my_bid = max(my_bid, highest_prev_bid + increment * 2) # Larger increment
            my_bid = max(my_bid, DAILY_SALARY * 1.2) # Ensure a very aggressive bid
        else: # Still be aggressive, but conserve budget if tight
            my_bid = max(my_bid, DAILY_SALARY * 1.1) # Ensure at least 10% above salary

    # Ensure bid does not exceed available budget
    # Always bid at least 1.0 to be considered a valid bid.
    my_bid = max(my_bid, 1.0)
    my_bid = min(my_bid, my_status['budget'])
    
    # If budget is critically low, I must bid everything I have to survive this day.
    # This is a last resort, if my calculated bid was less than my remaining budget
    # but my budget is too low to guarantee survival otherwise.
    if my_status['budget'] < DAILY_SALARY * 0.8 and day_context['day'] > 1:
         if my_bid < my_status['budget']:
             my_bid = my_status['budget'] # Bid everything to survive

    return my_bid
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

    # If no opponents, bid just enough to get water, save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Calculate total water demand and highest previous bid from opponents
    total_required_water = WATER_REQ
    highest_prev_bid = 0.0

    for opp in alive_opponents:
        total_required_water += opp['water_requirement']
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])

    # Base bid is what I'd typically pay for my full water requirement
    base_bid = DAILY_SALARY

    # Adjust bid based on my HP
    bid_multiplier = 1.0
    if my_status['hp'] <= 2: # Critical HP
        bid_multiplier = 1.5
    elif my_status['hp'] <= 5: # Low HP
        bid_multiplier = 1.2
    # If I have high HP and many days left, I can be slightly more conservative
    elif my_status['hp'] > (EPISODE_DAYS - day_context['day'] + 1) + 2:
        bid_multiplier = 0.9
    
    current_bid = base_bid * bid_multiplier

    # Adjust bid based on supply scarcity and opponent behavior
    can_all_get_full_water = day_context['supply'] >= total_required_water

    if not can_all_get_full_water:
        # High competition expected
        # Bid above highest previous bid to secure water
        if highest_prev_bid > 0:
            current_bid = max(current_bid, highest_prev_bid + (DAILY_SALARY * 0.1))
        current_bid = max(current_bid, base_bid * 1.1) # Ensure it's at least 10% above my base cost
    else:
        # Supply is abundant, can try to save money
        if highest_prev_bid > 0:
            # If opponents were bidding high, don't drop too much
            if highest_prev_bid > base_bid * 0.8:
                current_bid = max(current_bid, highest_prev_bid * 0.9)
            else: # Opponents were bidding low, I can bid lower
                current_bid = max(current_bid, base_bid * 0.7)
        else:
            # No previous bids, or all very low. Bid conservatively.
            current_bid = max(current_bid, base_bid * 0.6)

    # Ensure a reasonable minimum bid to actually win water
    min_effective_bid = DAILY_SALARY * 0.5
    current_bid = max(current_bid, min_effective_bid)

    # Cap bid by budget
    current_bid = min(current_bid, my_status['budget'])

    # Ensure bid is positive
    current_bid = max(current_bid, 0.01)

    return current_bid
"""
