# ============================================================
# Experiment: exp_073
# Agent: Cindy
# Source: exp_073
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid values relative to daily salary
    bid_low = DAILY_SALARY * 0.3
    bid_medium = DAILY_SALARY * 0.5
    bid_high = DAILY_SALARY * 0.7
    bid_critical = DAILY_SALARY * 0.9
    bid_desperate = DAILY_SALARY * 0.95 # Even higher for extreme cases

    # 1. No opponents: Bid minimally to save budget, guaranteed water.
    if num_alive_opponents == 0:
        return min(my_budget, max(1, WATER_REQ * 0.1))

    # 2. Survival mode: Prioritize getting water if HP is low or missed water yesterday.
    if my_no_water_days >= 1 or my_hp <= 2:
        if my_hp <= 1: # Extremely critical, bid very high
            return min(my_budget, bid_desperate)
        return min(my_budget, bid_critical) # Critical, bid high

    # 3. Assess supply vs demand to adjust bid based on competition intensity.
    total_req_by_alive_players = WATER_REQ + sum(o['water_requirement'] for o in alive_opponents)

    # If supply is abundant for everyone, bid lower to save budget.
    if current_supply >= total_req_by_alive_players:
        # If my HP is not perfect, still bid reasonably to secure water just in case.
        if my_hp <= 3:
            return min(my_budget, bid_medium)
        return min(my_budget, bid_low)

    # If supply is scarce (not enough for everyone's full requirement), competition will be higher.
    if num_alive_opponents == 1:
        # Direct competition. If supply is very tight for two players, bid higher.
        if current_supply < WATER_REQ * 1.5: 
            return min(my_budget, bid_high)
        return min(my_budget, bid_medium) # Standard competition bid

    if num_alive_opponents >= 2:
        # Multiple opponents and scarce supply, bid high due to intense competition.
        return min(my_budget, bid_high)

    # Default fallback bid if no specific condition is met (should ideally not be reached).
    return min(my_budget, bid_medium)
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.75

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.9: 
            if my_hp <= 3: 
                base_bid = max(DAILY_SALARY * 0.98, highest_prev_bid + 5)
            elif my_hp <= 5: 
                base_bid = max(DAILY_SALARY * 0.9, highest_prev_bid + 2)
            else: 
                base_bid = max(DAILY_SALARY * 0.8, highest_prev_bid + 1)
        elif highest_prev_bid >= DAILY_SALARY * 0.75: 
            if my_hp <= 3: 
                base_bid = max(DAILY_SALARY * 0.95, highest_prev_bid + 5)
            else: 
                base_bid = max(DAILY_SALARY * 0.78, highest_prev_bid + 2)
        else: 
            if my_hp <= 3: 
                base_bid = max(DAILY_SALARY * 0.9, highest_prev_bid + 10)
            elif my_hp <= 5: 
                base_bid = max(DAILY_SALARY * 0.7, highest_prev_bid + 5)
            else: 
                base_bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 1)
    else: 
        if my_hp <= 3:
            base_bid = DAILY_SALARY * 0.95
        elif my_hp <= 5:
            base_bid = DAILY_SALARY * 0.85
        else:
            base_bid = DAILY_SALARY * 0.7

    if current_day >= EPISODE_DAYS - 2 and my_hp <= 5:
        base_bid = max(base_bid, DAILY_SALARY * 0.98)

    if my_hp >= 9 and current_day < EPISODE_DAYS / 2:
        base_bid = min(base_bid, DAILY_SALARY * 0.7)

    bid = min(my_budget, base_bid)
    bid = max(bid, DAILY_SALARY * 0.2)

    return bid
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

    # If no opponents or only very weak ones, bid low
    if not alive_opponents or all(o['water_requirement'] == 0 for o in alive_opponents):
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Get yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.6 # Default bid

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP, bid aggressively
        base_bid = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 5: # Low HP
        base_bid = DAILY_SALARY * 0.75

    # Adjust bid based on day (late game push)
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    # Adjust bid based on supply scarcity
    if day_context['supply'] <= WATER_REQ * 1.5: # Supply is tight, likely only one or two full water allocations
        base_bid = max(base_bid, DAILY_SALARY * 0.7) # Increase bid for scarce water
        if my_status['hp'] <= 5: # Even more aggressive if HP is low and supply is tight
            base_bid = max(base_bid, DAILY_SALARY * 0.85)

    # React to highest previous bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest bid was very high, consider matching or slightly exceeding it if I need water
        if highest_prev_bid >= DAILY_SALARY * 0.7: # If opponents are bidding high
            if my_status['hp'] <= 5: # If I need water, try to outbid
                base_bid = max(base_bid, highest_prev_bid + 5)
            else: # If my HP is good, I might slightly increase but not overcommit
                base_bid = max(base_bid, highest_prev_bid * 0.9) # Don't overpay if not critical
        elif highest_prev_bid < DAILY_SALARY * 0.3 and my_status['hp'] > 5: # If opponents are bidding very low and I'm healthy, try to save money
            base_bid = min(base_bid, highest_prev_bid + 10) # Bid slightly above to win cheaply

    # Ensure bid doesn't exceed budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure bid is at least 0
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    TOTAL_DAYS = 10 # From meta_round_id['episode_days']

    # Base bid strategy
    # Start with a moderate bid, aiming to cover water cost and some profit
    base_bid = DAILY_SALARY * 0.5

    # Identify competitive opponents (excluding known weak ones like David/Eric)
    competitive_opponents = []
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive'] and opp_id not in ["David", "Eric"]:
            competitive_opponents.append(opp_data)

    num_competitive_players = len(competitive_opponents) + 1 # Include myself

    # 1. Adjust based on opponent's previous bids (focus on Alex as the main competitor)
    alex_status = opponents_status.get("Alex")
    if alex_status and alex_status['alive']:
        alex_prev_trace = alex_status.get('previous_trace', {})
        alex_prev_bid = alex_prev_trace.get('bid', 0.0)

        if alex_prev_bid > 0: # If Alex made a bid yesterday
            if my_status['hp'] <= 3: # Critical HP, need water desperately
                base_bid = max(base_bid, alex_prev_bid + 15) # Outbid Alex significantly
            elif my_status['hp'] <= 6: # Low HP
                base_bid = max(base_bid, alex_prev_bid + 8) # Slightly outbid Alex
            else: # Stable HP, but Alex is competitive
                base_bid = max(base_bid, alex_prev_bid * 1.05) # Small increase over Alex's bid

    # 2. Adjust based on my HP
    if my_status['hp'] <= 2: # Very critical HP
        base_bid = max(base_bid, DAILY_SALARY * 0.98)
    elif my_status['hp'] <= 4: # Critical HP
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    elif my_status['hp'] <= 6 and day_context['day'] > TOTAL_DAYS / 2: # Mid-late game, slightly low HP
        base_bid = max(base_bid, DAILY_SALARY * 0.65)

    # 3. Adjust based on supply scarcity
    # Calculate total water needed by competitive players
    total_water_needed_by_competitive = WATER_REQ * num_competitive_players
    
    if day_context['supply'] < total_water_needed_by_competitive:
        # Scarcity: increase bid
        # The more scarce, the higher the multiplier, up to 40% increase
        scarcity_factor = 1.0 + (total_water_needed_by_competitive - day_context['supply']) / total_water_needed_by_competitive * 0.4
        base_bid *= scarcity_factor
    elif day_context['supply'] >= total_water_needed_by_competitive + WATER_REQ: # Abundant supply (+1 full water_req buffer)
        # Abundant supply: slightly reduce bid if not desperate
        if my_status['hp'] > 5:
            base_bid *= 0.9
        else: # Still need water, don't reduce too much
            base_bid *= 0.95

    # 4. Adjust for end-game
    current_day = day_context['day']
    days_left = TOTAL_DAYS - current_day
    if days_left <= 2:
        if my_status['hp'] < 5: # End game, low HP, must survive
            base_bid = max(base_bid, DAILY_SALARY * 0.99)
        elif my_status['budget'] > DAILY_SALARY * 2: # End game, good budget, can afford to be aggressive to win
            base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif days_left <= 5 and my_status['hp'] > 8: # Mid-late game, good HP, can save some budget
        base_bid *= 0.95


    # Ensure bid does not exceed budget and is non-negative
    final_bid = min(my_status['budget'], base_bid)
    final_bid = max(0.0, final_bid)
    
    # Round to two decimal places for consistency
    return round(final_bid, 2)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 
    SURVIVAL_HP_THRESHOLD = 3
    MODERATE_HP_THRESHOLD = 6 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    total_water_needed_by_opponents = sum(o['water_requirement'] for o in alive_opponents)
    total_water_needed_by_all = WATER_REQ + total_water_needed_by_opponents

    num_active_agents = len(alive_opponents) + 1
    
    # Handle potential division by zero if num_active_agents is 0 (should not happen if 'my_status' implies I'm active)
    # If no opponents, num_active_agents is 1.
    available_water_per_agent = day_context['supply'] / num_active_agents
    is_supply_tight = available_water_per_agent < WATER_REQ

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid = DAILY_SALARY * 0.5 

    if my_status['hp'] <= SURVIVAL_HP_THRESHOLD or my_status['no_water_days'] > 0:
        bid = DAILY_SALARY * 0.95 
        if is_supply_tight:
            bid = DAILY_SALARY * 1.1 
    elif my_status['hp'] <= MODERATE_HP_THRESHOLD:
        if yesterday_bids:
            max_opp_bid = max(yesterday_bids)
            avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids)
            if is_supply_tight:
                bid = max(DAILY_SALARY * 0.75, max_opp_bid + 10)
            else:
                bid = max(DAILY_SALARY * 0.6, avg_opp_bid + 5)
        else:
            bid = DAILY_SALARY * 0.7 if is_supply_tight else DAILY_SALARY * 0.6
    else:
        if yesterday_bids:
            max_opp_bid = max(yesterday_bids)
            avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids)
            if is_supply_tight:
                bid = max(DAILY_SALARY * 0.6, avg_opp_bid * 1.1)
            else:
                bid = max(DAILY_SALARY * 0.4, avg_opp_bid * 0.9)
        else:
            bid = DAILY_SALARY * 0.6 if is_supply_tight else DAILY_SALARY * 0.45

    final_bid = max(0.01, min(my_status['budget'], bid))

    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_SUPPLY = 25.0
    MIN_SUPPLY = 15.0
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Emergency mode: If HP is critically low, bid very high to survive
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 1.15)

    # If no opponents, bid minimal to save budget
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

    # Base bid calculation
    base_bid = DAILY_SALARY * 0.6 # Starting point, e.g., 90 for Cindy

    # Adjust bid based on opponent's previous aggressive bidding
    if max_yesterday_bid > DAILY_SALARY * 0.7: # If opponents bid significantly high yesterday (e.g., > 105)
        bid = max_yesterday_bid + 5.0 # Try to outbid them
    else:
        bid = max(base_bid, max_yesterday_bid * 1.05) # Slightly above their max if it's not too high, or base bid

    # Adjust bid based on supply scarcity
    # supply_factor is 0 when supply is max, 1 when supply is min
    supply_factor = (MAX_SUPPLY - day_context['supply']) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_adjustment = supply_factor * (DAILY_SALARY * 0.4) # Add up to 40% of salary for scarcity
    bid += supply_adjustment

    # If HP is moderately low, ensure a stronger bid
    if my_status['hp'] <= 4:
        bid = max(bid, DAILY_SALARY * 0.85) # Ensure at least 127.5 bid

    # Final bid must not exceed budget
    final_bid = min(my_status['budget'], bid)

    # Ensure bid is at least a small positive amount if budget allows and water is needed
    if final_bid <= 0 and my_status['budget'] > 0 and my_status['hp'] < EPISODE_DAYS: 
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.1)

    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    TOTAL_DAYS = 10

    # Strategy parameters based on the example and my context
    CRITICAL_HP_THRESHOLD = 3
    HIGH_BID_THRESHOLD_RATIO = 0.85  # Opponent bids >= 127.5
    BLEED_BID_RATIO = 0.3            # Bid 45 to let them win and drain budget
    CRITICAL_BID_RATIO = 0.95        # Bid 142.5 when HP is critical
    MODERATE_BID_BASE_RATIO = 0.5    # Base bid 75 for moderate competition
    MODERATE_BID_INCREMENT = 1.5     # Increment by 1.5 over opponent's bid
    DEFAULT_LOW_HP_BID_RATIO = 0.9   # Bid 135 if HP <= 2 and no specific opponent trace
    DEFAULT_NORMAL_BID_RATIO = 0.55  # Default bid 82.5
    NO_OPPONENT_BID_RATIO = 0.1      # Bid 15 if no alive opponents

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimum to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * NO_OPPONENT_BID_RATIO)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # If there are yesterday's bids from opponents
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If opponents are bidding very high
        if highest_prev_bid >= DAILY_SALARY * HIGH_BID_THRESHOLD_RATIO:
            # If my HP is good, adopt 'bleed' strategy
            if my_status['hp'] > CRITICAL_HP_THRESHOLD:
                return min(my_status['budget'], DAILY_SALARY * BLEED_BID_RATIO)
            # If my HP is critical, bid very high to survive
            return min(my_status['budget'], DAILY_SALARY * CRITICAL_BID_RATIO)
        # If opponents are bidding moderately
        else:
            # Bid slightly above their highest previous bid, with a floor
            return min(my_status['budget'], max(DAILY_SALARY * MODERATE_BID_BASE_RATIO, highest_prev_bid + MODERATE_BID_INCREMENT))

    # If no yesterday's bids (e.g., first day or opponents didn't bid)
    # Prioritize survival if HP is low
    if my_status['hp'] <= CRITICAL_HP_THRESHOLD:
        return min(my_status['budget'], DAILY_SALARY * DEFAULT_LOW_HP_BID_RATIO)
    
    # Otherwise, make a default moderate bid
    return min(my_status['budget'], DAILY_SALARY * DEFAULT_NORMAL_BID_RATIO)
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
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1) 

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_bid = DAILY_SALARY * 0.5 

    if my_status['hp'] <= 2: 
        current_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: 
        current_bid = DAILY_SALARY * 0.75
    
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['budget'] > DAILY_SALARY * 1.5:
        current_bid = max(current_bid, DAILY_SALARY * 0.85)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: 
                current_bid = max(current_bid, DAILY_SALARY * 0.6) 
            else: 
                current_bid = max(current_bid, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            current_bid = max(current_bid, highest_prev_bid + 2)
        else:
            water_units_available = int(day_context['supply'] // WATER_REQ)
            total_players = len(alive_opponents) + 1
            if water_units_available < total_players and water_units_available > 0: 
                current_bid = max(current_bid, highest_prev_bid + 10)
            else:
                current_bid = max(current_bid, highest_prev_bid * 1.1)

    final_bid = min(my_status['budget'], current_bid)
    
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

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    remaining_days = EPISODE_DAYS - current_day + 1

    critical_hp_threshold = 3
    critical_no_water_days_threshold = 1

    is_critical = (my_hp <= critical_hp_threshold) or (my_no_water_days >= critical_no_water_days_threshold)

    yesterday_bids = []
    total_opponent_water_req = 0
    for opp in alive_opponents:
        total_opponent_water_req += opp['water_requirement']
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    base_bid = DAILY_SALARY * 0.55

    if is_critical:
        aggressive_bid_factor = 0.95
        if my_hp <= 1:
            aggressive_bid_factor = 1.0
        base_bid = max(base_bid, DAILY_SALARY * aggressive_bid_factor)
    else:
        if my_hp > WATER_REQ * 2:
             base_bid = DAILY_SALARY * 0.4
        elif my_hp > WATER_REQ:
             base_bid = DAILY_SALARY * 0.5

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        if is_critical:
            base_bid = max(base_bid, min(max_prev_bid + 5, DAILY_SALARY * 1.1))
        else:
            base_bid = max(base_bid, avg_prev_bid * 1.05)
            if my_hp > WATER_REQ * 2 and avg_prev_bid > DAILY_SALARY * 0.7:
                 base_bid = min(base_bid, avg_prev_bid * 0.9)

    total_demand_estimate = WATER_REQ + total_opponent_water_req
    if current_supply < total_demand_estimate * 0.75:
        base_bid *= 1.15
    elif current_supply < total_demand_estimate * 0.9:
        base_bid *= 1.05
    elif current_supply > total_demand_estimate * 1.5:
        base_bid *= 0.85
    elif current_supply > total_demand_estimate * 1.1:
        base_bid *= 0.95

    final_bid = min(my_budget, base_bid)
    final_bid = max(1.0, final_bid)

    return final_bid
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

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Urgency increases as the game progresses
    urgency_factor = 1.0 + (day_context['day'] / EPISODE_DAYS) * 0.3 

    # Base bid, adjusted by urgency
    base_bid = DAILY_SALARY * 0.6 * urgency_factor

    # Adjust bid based on my HP and no_water_days
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        # Critical HP or consecutive no water days, bid very aggressively
        bid = DAILY_SALARY * 0.95 * urgency_factor
    elif my_status['hp'] >= 8:
        # Healthy, can afford to be a bit less aggressive if competition isn't too high
        bid = DAILY_SALARY * 0.5 * urgency_factor
    else:
        bid = base_bid

    # Analyze yesterday's bids from opponents' previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest previous bid was significant, ensure we bid above it
        # Add a small increment to win against similar bids
        if highest_prev_bid >= DAILY_SALARY * 0.7: 
            bid = max(bid, highest_prev_bid + 5)
        else: 
            bid = max(bid, highest_prev_bid + 1)
    
    # Ensure bid is within budget
    final_bid = min(my_status['budget'], bid)
    
    # Ensure a minimum bid to secure water and signal presence
    if final_bid < DAILY_SALARY * 0.1:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.1)

    return final_bid
"""
