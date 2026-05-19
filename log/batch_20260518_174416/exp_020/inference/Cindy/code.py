# ============================================================
# Experiment: exp_020
# Agent: Cindy
# Source: exp_020
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Default bid (when not urgent and supply is moderate)
    bid_amount = DAILY_SALARY * 0.4 # 60

    # Scenario 1: No opponents alive
    if num_alive_opponents == 0:
        # Secure water cheaply, but ensure it's enough to win if multiple agents were inactive
        return min(my_status['budget'], WATER_REQ * 2) # e.g., 26

    # Scenario 2: Urgent need for water (HP is low)
    if my_status['hp'] <= 1: # Will die if no water today
        bid_amount = DAILY_SALARY * 0.95 # 142.5 - almost max bid
    elif my_status['hp'] == 2: # Very critical, 1 day left before critical
        bid_amount = DAILY_SALARY * 0.8 # 120
    elif my_status['hp'] == 3: # Critical, 2 days left
        bid_amount = DAILY_SALARY * 0.65 # 97.5

    # Scenario 3: Supply scarcity and competition
    supply = day_context['supply']

    if supply <= WATER_REQ + 2: # Very tight supply, likely only enough for one person (15 units is 13+2)
        # If supply is very low, it's a direct fight. Bid aggressively if needed.
        if my_status['hp'] > 1: # If not already maxed out by HP urgency
             bid_amount = max(bid_amount, DAILY_SALARY * 0.75) # 112.5
    elif supply > WATER_REQ + 2 and supply <= WATER_REQ * 2: # Moderate supply, maybe enough for two
        if my_status['hp'] > 2: # If not very urgent, still be competitive
            bid_amount = max(bid_amount, DAILY_SALARY * 0.55) # 82.5
    # If supply is high (e.g., > WATER_REQ * 2), and my HP is good, the default bid_amount handles it.

    # Scenario 4: End of the game
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] > 0: # Last 2 days and I need water
        if my_status['hp'] <= 2: # If I will die soon, bid almost everything
            bid_amount = my_status['budget']
        else: # If I still have some buffer, but it's end game, bid high
            bid_amount = max(bid_amount, DAILY_SALARY * 0.8) # 120

    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], bid_amount)

    # Ensure bid is at least 1 if water is needed, otherwise 0
    if final_bid <= 0 and my_status['hp'] > 0:
        final_bid = 1
    elif final_bid < 0:
        final_bid = 0

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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    bid_critical_hp = DAILY_SALARY * 0.95 
    bid_low_hp = DAILY_SALARY * 0.85 
    bid_normal_hp_base = DAILY_SALARY * 0.65 
    bid_minimal = DAILY_SALARY * 0.1 

    days_remaining = EPISODE_DAYS - current_day + 1

    if not alive_opponents:
        return min(my_budget, bid_minimal)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    bid_amount = 0
    if my_hp <= 2: 
        bid_amount = bid_critical_hp
    elif my_hp <= 5: 
        bid_amount = bid_low_hp
        if highest_prev_bid > 0:
            bid_amount = max(bid_amount, highest_prev_bid + 5)
    else: 
        bid_amount = bid_normal_hp_base

        if supply >= WATER_REQ * 1.8: 
            if num_alive_opponents > 1:
                bid_amount = min(bid_amount, DAILY_SALARY * 0.55)
                if highest_prev_bid > 0:
                    bid_amount = max(bid_amount, highest_prev_bid * 0.9)
            else:
                bid_amount = min(bid_amount, DAILY_SALARY * 0.4)
                if highest_prev_bid > 0:
                    bid_amount = max(bid_amount, highest_prev_bid * 0.95)

        elif supply < WATER_REQ * 1.2: 
            bid_amount = max(bid_amount, DAILY_SALARY * 0.75)
            if highest_prev_bid > 0:
                bid_amount = max(bid_amount, highest_prev_bid + 2)

        if highest_prev_bid > DAILY_SALARY * 0.6: 
            bid_amount = max(bid_amount, highest_prev_bid + 1)

        if days_remaining <= 3 and my_budget > DAILY_SALARY * 3:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.8)
        elif my_budget < DAILY_SALARY * 1.5 and my_hp > 5:
            bid_amount = min(bid_amount, DAILY_SALARY * 0.5)

    final_bid = min(my_budget, bid_amount)

    if my_hp == 10:
        return 0

    if my_budget <= 0:
        return 0

    if final_bid < 1:
        return min(my_budget, DAILY_SALARY * 0.2)

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_supply = day_context['supply']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.3)

    base_bid = 0.0
    if my_hp <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 5:
        base_bid = DAILY_SALARY * 0.8
    else:
        base_bid = DAILY_SALARY * 0.65

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_bid = base_bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_hp > 3:
                current_bid = max(current_bid, highest_prev_bid + 5.0)
            else:
                current_bid = max(current_bid, highest_prev_bid + 10.0)
        else:
            current_bid = max(current_bid, highest_prev_bid + 1.0)

    if current_supply < WATER_REQ * 1.2:
        current_bid = max(current_bid, DAILY_SALARY * 0.9)
    elif current_supply > WATER_REQ * 1.8:
        if my_hp > 5:
            current_bid = min(current_bid, DAILY_SALARY * 0.5)
        else:
            current_bid = max(current_bid, DAILY_SALARY * 0.6)

    current_bid = max(1.0, current_bid)
    current_bid = min(my_budget, current_bid)

    return current_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta_round_state['episode_days']

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid calculation: Start with a reasonable fraction of daily salary
    base_bid = DAILY_SALARY * 0.6

    # --- Dynamic adjustments ---

    # 1. HP-based desperation
    if my_hp <= 2: # Very low HP, must get water
        base_bid = DAILY_SALARY * 0.95
    elif my_hp == 3: # Low HP, need water
        base_bid = DAILY_SALARY * 0.8
    elif my_hp > 3 and my_no_water_days > 0: # Not critical HP, but missed water yesterday
        base_bid = DAILY_SALARY * 0.75 # Increase a bit to avoid missing again

    # 2. Opponent yesterday's bids (from previous_trace)
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace')
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        max_opp_bid_yesterday = max(yesterday_bids)
        avg_opp_bid_yesterday = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents were very aggressive, I need to be more aggressive
        if max_opp_bid_yesterday >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, max_opp_bid_yesterday + 5.0) # Bid slightly above
        # If opponents were conservative, I can afford to be more conservative but still aim to win
        elif max_opp_bid_yesterday < DAILY_SALARY * 0.5:
            base_bid = max(base_bid, avg_opp_bid_yesterday + 2.0)
        else: # Moderate bids, try to be slightly above average
            base_bid = max(base_bid, avg_opp_bid_yesterday + 2.0)

    # 3. Supply vs Demand
    total_water_needed_by_alive = WATER_REQ # My requirement
    for opp in alive_opponents:
        total_water_needed_by_alive += opp['water_requirement']

    # If supply is tight, increase bid
    if current_supply < total_water_needed_by_alive:
        # How tight is it? Avoid division by zero if total_water_needed_by_alive is 0, though unlikely.
        if total_water_needed_by_alive > 0:
            shortage_ratio = total_water_needed_by_alive / current_supply
            if shortage_ratio > 1.5: # Very tight
                base_bid *= 1.2
            elif shortage_ratio > 1.2: # Moderately tight
                base_bid *= 1.1
    elif current_supply >= total_water_needed_by_alive * 1.5: # Abundant supply
        base_bid *= 0.9 # Can afford to bid lower

    # 4. End game strategy
    remaining_days = EPISODE_DAYS - current_day + 1
    if remaining_days <= 2: # Last few days, prioritize survival over budget
        if my_hp <= 5: # If HP is not great, bid very high
            base_bid = DAILY_SALARY * 1.1 # Can exceed salary if budget allows
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.7)

    # Ensure bid is not negative or zero if budget is low, minimum bid is 1.0 to participate.
    final_bid = max(1.0, base_bid)

    # Cap the bid by current budget
    final_bid = min(my_budget, final_bid)

    # If budget is 0, I cannot bid.
    if my_budget == 0:
        return 0.0

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

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    eric_alive = False
    eric_yesterday_bid = None

    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            if opp_id == "Eric":
                eric_alive = True
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
                if opp_id == "Eric":
                    eric_yesterday_bid = prev['bid']

    if my_status['no_water_days'] > 0 or my_status['hp'] <= 3:
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            return min(my_status['budget'], max(DAILY_SALARY * 0.95, highest_prev_bid + 5))
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.95)

    base_moderate_bid = DAILY_SALARY * 0.55

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if eric_alive:
            if eric_yesterday_bid is not None and eric_yesterday_bid > DAILY_SALARY * 0.8:
                return min(my_status['budget'], max(base_moderate_bid, eric_yesterday_bid + 5))
            elif eric_yesterday_bid is not None:
                return min(my_status['budget'], max(base_moderate_bid, highest_prev_bid + 2))
            else:
                return min(my_status['budget'], max(base_moderate_bid, highest_prev_bid * 1.05 + 5))
        
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            return min(my_status['budget'], max(base_moderate_bid, highest_prev_bid + 2))
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            return min(my_status['budget'], max(base_moderate_bid, highest_prev_bid + 1))
        else:
            return min(my_status['budget'], base_moderate_bid)

    return min(my_status['budget'], base_moderate_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid values derived from daily salary and opponent history
    base_bid = DAILY_SALARY * 0.9  # A competitive starting bid (135)
    high_bid = DAILY_SALARY * 1.1  # Aggressive bid (165)
    very_high_bid = DAILY_SALARY * 1.25 # More aggressive (187.5)
    survival_bid = DAILY_SALARY * 1.3 # Max aggression for survival (195)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])
    
    max_yesterday_bid = 0.0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    my_current_bid = base_bid

    # --- Bidding Logic based on HP and recent competition ---

    # Critical health: Prioritize survival at all costs (within budget)
    if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1:
        # Bid very high, ensuring to outbid yesterday's max by a margin
        my_current_bid = max(survival_bid, max_yesterday_bid + 5.0)
    # Low health: Be aggressive
    elif my_status['hp'] <= 5:
        # Bid high, slightly above yesterday's max
        my_current_bid = max(very_high_bid, max_yesterday_bid + 2.0)
    # Moderate health: Be competitive, react to market
    elif my_status['hp'] <= 7:
        # Bid competitively, slightly above yesterday's max
        my_current_bid = max(high_bid, max_yesterday_bid + 1.0)
    # Good health: Can be a bit more strategic, but still aim to win
    else:
        # If no strong competition yesterday, bid moderately but firmly
        if max_yesterday_bid < DAILY_SALARY * 0.8:
            my_current_bid = DAILY_SALARY * 0.85
        # If there was competition, bid slightly above it to secure water
        else:
            my_current_bid = max(base_bid, max_yesterday_bid + 0.5)

    # Ensure bid is at least a minimum to be considered serious and not fall into 'David' territory
    my_current_bid = max(my_current_bid, DAILY_SALARY * 0.2)

    # Cap bid by current budget
    final_bid = min(my_current_bid, my_status['budget'])

    # Ensure bid is not negative
    final_bid = max(0.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    HP_THRESHOLD_CRITICAL = 2 
    HP_THRESHOLD_HIGH_PRESSURE = 4 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    opponent_critical_hp_count = 0
    opponent_high_pressure_hp_count = 0

    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])
        
        if opp['hp'] <= HP_THRESHOLD_CRITICAL:
            opponent_critical_hp_count += 1
        elif opp['hp'] <= HP_THRESHOLD_HIGH_PRESSURE:
            opponent_high_pressure_hp_count += 1

    bid = DAILY_SALARY * 0.55 

    if my_status['hp'] <= HP_THRESHOLD_CRITICAL:
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= HP_THRESHOLD_HIGH_PRESSURE:
        bid = DAILY_SALARY * 0.8
    else:
        bid = DAILY_SALARY * 0.4 

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        if my_status['hp'] <= HP_THRESHOLD_CRITICAL:
            bid = max(bid, max_prev_bid + 5)
        elif opponent_critical_hp_count > 0:
            bid = max(bid, max_prev_bid + 2)
        elif my_status['hp'] <= HP_THRESHOLD_HIGH_PRESSURE:
            bid = max(bid, max_prev_bid + 1)
        else:
            bid = max(bid, max_prev_bid + 0.5)

    final_bid = min(my_status['budget'], bid)
    final_bid = max(0.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQUIREMENT = 13
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

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    is_urgent = my_status['hp'] <= 2 or my_status['no_water_days'] >= 1
    
    bid = 0.0
    if is_urgent:
        bid = DAILY_SALARY * 0.95
        if day_context['day'] >= EPISODE_DAYS - 2:
            bid = DAILY_SALARY * 1.05
    else:
        if highest_prev_bid > DAILY_SALARY * 0.8:
            if my_status['hp'] > 5:
                bid = DAILY_SALARY * 0.35
            else:
                bid = max(DAILY_SALARY * 0.6, highest_prev_bid + 5.0)
        elif highest_prev_bid > DAILY_SALARY * 0.4:
            bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.0)
        else:
            bid = DAILY_SALARY * 0.55
            
    bid = max(1.0, bid)
    return min(my_status['budget'], bid)
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

    # If no opponents are alive, bid just enough to secure water and save budget.
    if not alive_opponents:
        return min(my_status['budget'], WATER_REQ * 2) # Bid a small premium above cost

    # Collect yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine highest previous bid. If none, set a competitive baseline (e.g., David's average)
    # David's average bid was ~114.46, which is ~0.76 of 150.
    highest_prev_bid = DAILY_SALARY * 0.75 
    if yesterday_bids:
        highest_prev_bid = max(highest_prev_bid, max(yesterday_bids))

    # Calculate number of agents needing water (including myself)
    num_competitors = len(alive_opponents) + 1
    # Calculate how many agents can get full water given current supply
    slots_for_full_water = int(day_context['supply'] // WATER_REQ)

    # Base bid strategy
    current_bid = DAILY_SALARY * 0.55 # A moderate starting bid

    # Adjust bid based on my HP and no_water_days
    if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1:
        # Desperate situation: bid very high to secure water
        current_bid = DAILY_SALARY * 0.95
        # If highest_prev_bid was already high, ensure we outbid it
        if highest_prev_bid > DAILY_SALARY * 0.8:
            current_bid = max(current_bid, highest_prev_bid + 2.0)
    elif day_context['day'] >= EPISODE_DAYS - 2:
        # Late game: prioritize survival, bid high
        current_bid = DAILY_SALARY * 0.9
        if highest_prev_bid > DAILY_SALARY * 0.7:
            current_bid = max(current_bid, highest_prev_bid + 1.5)
    else:
        # Healthy state: adjust based on competition and supply
        if slots_for_full_water < num_competitors:
            # High competition for water
            current_bid = max(DAILY_SALARY * 0.65, highest_prev_bid + 1.5)
        else:
            # Less competition, can afford to be slightly less aggressive
            current_bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 0.5)

    # Specific adjustment for David, if he is alive and strong
    if 'David' in opponents_status and opponents_status['David']['alive']:
        # If David has a high budget and is a strong competitor, be prepared to outbid him
        # David's max bid was 150.62, so he can go slightly above DAILY_SALARY
        if opponents_status['David']['budget'] > my_status['budget'] * 0.7 and highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] <= 5 or day_context['day'] >= EPISODE_DAYS - 3:
                 current_bid = max(current_bid, DAILY_SALARY * 1.05) # Aggressively target David if desperate

    # Ensure bid does not exceed available budget
    final_bid = min(my_status['budget'], current_bid)

    # Ensure bid is at least 0
    return max(0.0, final_bid)
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    strong_opponents_bids = []
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive'] and (opp_id == "Alex" or opp_id == "Eric"):
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                strong_opponents_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.6 

    if my_hp <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4:
        base_bid = DAILY_SALARY * 0.8
    elif my_hp >= 8:
        base_bid = DAILY_SALARY * 0.5

    if strong_opponents_bids:
        max_yesterday_strong_bid = max(strong_opponents_bids)
        
        if max_yesterday_strong_bid >= DAILY_SALARY * 0.8:
            if my_hp <= 3:
                base_bid = max(base_bid, max_yesterday_strong_bid + 5)
            else:
                base_bid = max(base_bid, max_yesterday_strong_bid + 1)
        elif max_yesterday_strong_bid >= DAILY_SALARY * 0.5:
            base_bid = max(base_bid, max_yesterday_strong_bid + 0.5)
    
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2:
        if my_budget >= DAILY_SALARY * 1.5:
            base_bid = max(base_bid, DAILY_SALARY * 0.9)
        elif my_hp <= 3:
            base_bid = max(base_bid, DAILY_SALARY * 0.98)
    
    final_bid = max(1.0, min(my_budget, base_bid))
    
    return final_bid
"""
