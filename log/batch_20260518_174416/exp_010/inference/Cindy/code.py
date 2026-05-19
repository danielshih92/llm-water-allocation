# ============================================================
# Experiment: exp_010
# Agent: Cindy
# Source: exp_010
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
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_budget, 1) 

    CRITICAL_HP_THRESHOLD = 2 
    if my_hp <= CRITICAL_HP_THRESHOLD:
        slots_available = int(current_supply // WATER_REQ)
        if slots_available <= 1: 
            return min(my_budget, DAILY_SALARY * 0.95) 
        else: 
            return min(my_budget, DAILY_SALARY * 0.8)

    yesterday_bids = []
    opponent_water_requirements = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])
        opponent_water_requirements.append(opp['water_requirement'])

    estimated_slots = int(current_supply // WATER_REQ)
    if estimated_slots == 0:
        estimated_slots = 1 

    very_tight_supply = (estimated_slots <= 1 and num_alive_opponents >= 1) or \
                        (estimated_slots == 2 and num_alive_opponents >= 2)

    is_late_game = current_day >= EPISODE_DAYS * 0.7 

    base_bid = DAILY_SALARY * 0.5 

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)

        if very_tight_supply:
            if max_yesterday_bid >= DAILY_SALARY * 0.7:
                base_bid = max(base_bid, max_yesterday_bid + 5)
            else:
                base_bid = max(base_bid, avg_yesterday_bid * 1.2)
            
            if is_late_game:
                base_bid = max(base_bid, DAILY_SALARY * 0.75)

        else:
            if max_yesterday_bid >= DAILY_SALARY * 0.8:
                if my_hp > CRITICAL_HP_THRESHOLD + 1 and not is_late_game:
                    base_bid = min(base_bid, max_yesterday_bid * 0.8)
                else:
                    base_bid = max(base_bid, max_yesterday_bid * 0.9)
            else:
                base_bid = max(base_bid, avg_yesterday_bid + 2)
                if is_late_game:
                    base_bid = max(base_bid, DAILY_SALARY * 0.6)

    else:
        if very_tight_supply:
            base_bid = DAILY_SALARY * 0.7
        else:
            base_bid = DAILY_SALARY * 0.5 

    final_bid = max(1, base_bid)

    return min(my_budget, final_bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQ = 13
    MY_DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    current_day = day_context['day']

    # --- Step 1: Determine a base bid based on my HP and general competitiveness ---
    # Default conservative bid
    bid_value = MY_DAILY_SALARY * 0.5 

    if my_status['hp'] <= 2: # Critical HP
        bid_value = MY_DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP
        bid_value = MY_DAILY_SALARY * 0.8

    # --- Step 2: React to opponents' previous bids ---
    highest_prev_bid = 0.0
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                highest_prev_bid = max(highest_prev_bid, prev_trace['bid'])

    if highest_prev_bid > 0:
        if my_status['hp'] > 4: # Healthy, try to outbid slightly
            bid_value = max(bid_value, highest_prev_bid + 2)
        else: # Less healthy, be more aggressive
            bid_value = max(bid_value, highest_prev_bid + 5)
    else:
        # If no previous bids or all were 0, ensure a reasonable bid
        bid_value = max(bid_value, MY_DAILY_SALARY * 0.4) # Ensure a minimum competitive bid even without prior info

    # --- Step 3: Late game survival override ---
    # If it's the last few days and my HP is critical, bid very high
    if current_day >= EPISODE_DAYS - 2 and my_status['hp'] <= 3:
        bid_value = MY_DAILY_SALARY * 1.0 # Bid full salary if needed

    # --- Step 4: Budget constraint ---
    final_bid = min(my_status['budget'], bid_value)

    # --- Step 5: Ensure a positive minimum bid ---
    # If budget is 0, bid 0.01 (the minimum allowed positive bid).
    # Otherwise, ensure the bid is at least 0.01.
    if my_status['budget'] <= 0:
        final_bid = 0.01
    else:
        final_bid = max(0.01, final_bid)

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

    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid values derived from example, scaled for my DAILY_SALARY
    BID_NO_OPPONENT = DAILY_SALARY * 0.4
    BID_HIGH_PRESSURE_HP_HIGH = DAILY_SALARY * 0.3
    BID_HIGH_PRESSURE_HP_LOW = DAILY_SALARY * 0.95
    BID_MODERATE_PRESSURE_BASE = DAILY_SALARY * 0.5
    BID_INCREMENT = 1.5
    BID_NO_TRACE_HP_LOW = DAILY_SALARY * 0.9
    BID_NO_TRACE_DEFAULT = DAILY_SALARY * 0.55
    HIGH_BID_THRESHOLD_FACTOR = 0.85 # Threshold for what is considered a 'high' opponent bid

    # --- Step 1: Handle no opponents ---
    if not alive_opponents:
        return min(my_status['budget'], BID_NO_OPPONENT)

    # --- Step 2: Analyze yesterday's bids from opponents ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    calculated_bid = 0.0

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # Check if the highest previous bid indicates high competition
        if highest_prev_bid >= DAILY_SALARY * HIGH_BID_THRESHOLD_FACTOR:
            if my_status['hp'] > 3: # If HP is good, try to conserve in a bidding war
                calculated_bid = BID_HIGH_PRESSURE_HP_HIGH
            else: # If HP is low or no_water_days, I must secure water
                calculated_bid = BID_HIGH_PRESSURE_HP_LOW
        else:
            # If highest bid was not extremely high, try to win by a small margin
            calculated_bid = max(BID_MODERATE_PRESSURE_BASE, highest_prev_bid + BID_INCREMENT)
    else:
        # If no previous bids from opponents (e.g., first day or opponents died)
        if my_status['hp'] <= 2 or my_status['no_water_days'] > 0: # If HP is low or no water, bid high for survival
            calculated_bid = BID_NO_TRACE_HP_LOW
        else: # Otherwise, bid moderately
            calculated_bid = BID_NO_TRACE_DEFAULT

    # --- Step 3: Adjust bid based on supply scarcity and number of competitors --- 
    # Calculate how many full WATER_REQ units can be satisfied from current_supply
    potential_full_fills = int(current_supply // WATER_REQ)

    # If supply is very tight (e.g., less than 2 full fills, and more than 1 competitor)
    if potential_full_fills < 2 and num_alive_opponents >= 1:
        calculated_bid *= 1.15 # Increase bid due to high competition
    elif potential_full_fills >= num_alive_opponents + 1: # If supply is abundant
        calculated_bid *= 0.85 # Decrease bid to save budget

    # --- Step 4: Final day adjustments for survival ---
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last 2 days, survival is paramount
        if my_status['hp'] <= 5: # If HP is not great, bid very aggressively
            calculated_bid = DAILY_SALARY * 0.99
        else: # If HP is good, still ensure water
            calculated_bid = max(calculated_bid, DAILY_SALARY * 0.7)

    # --- Step 5: Final constraints --- 
    final_bid = max(1.0, min(my_status['budget'], calculated_bid))

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

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    competitive_bid_base = DAILY_SALARY * 0.7

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        if max_prev_bid > DAILY_SALARY * 0.6:
            competitive_bid_base = max_prev_bid + 5
        else:
            competitive_bid_base = max(competitive_bid_base, max_prev_bid + 10)

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']

    final_bid = competitive_bid_base

    if my_hp <= 2:
        final_bid = DAILY_SALARY * 0.95
        if current_day > EPISODE_DAYS / 2 and my_budget > DAILY_SALARY * 2:
            final_bid = DAILY_SALARY * 1.1
    elif my_hp <= 5:
        final_bid = max(final_bid, DAILY_SALARY * 0.8)
        final_bid += 5
    else:
        final_bid = max(final_bid, DAILY_SALARY * 0.65)
        if my_budget > DAILY_SALARY * 3:
            final_bid += 10

    final_bid = max(1.0, min(my_budget, final_bid))

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
    num_alive_competitors = len(alive_opponents) + 1 # Including myself

    # If I'm the only one left, bid minimal to secure water.
    if num_alive_competitors == 1:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid strategy based on meta-round context: high bids generally lead to survival.
    # Start with a moderately high bid, around 70% of daily salary.
    base_bid = DAILY_SALARY * 0.7

    # Critical HP adjustment: If HP is very low, bid very aggressively.
    if my_status['hp'] <= 0: # At 0 or negative, will die without water
        base_bid = min(my_status['budget'], DAILY_SALARY * 0.98) # Bid almost full salary if possible
    elif my_status['hp'] <= 3: # Low HP, prioritize water
        base_bid = max(base_bid, DAILY_SALARY * 0.85) # Ensure a strong bid

    # Adjust based on previous day's highest bid
    # If opponents bid high, I should respond.
    if highest_prev_bid > 0:
        # If previous highest bid was very high (e.g., > 80% of salary), I need to be competitive.
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, highest_prev_bid + (DAILY_SALARY * 0.05))
        # If previous highest bid was moderate, I can be slightly more conservative if my HP is good.
        elif my_status['hp'] > 5:
            base_bid = max(base_bid, highest_prev_bid + (DAILY_SALARY * 0.02))
        else: # HP is not great, need to be more competitive
            base_bid = max(base_bid, highest_prev_bid + (DAILY_SALARY * 0.05))

    # Adjust for supply scarcity
    # Calculate total water demand from all alive agents (including myself)
    total_water_demand_from_alive = sum(o['water_requirement'] for o in alive_opponents) + WATER_REQ
    
    if day_context['supply'] < total_water_demand_from_alive:
        # Scarcity, increase bid pressure
        base_bid = max(base_bid, DAILY_SALARY * 0.75)
        if my_status['hp'] <= 5: # Critical scarcity and low HP
            base_bid = max(base_bid, DAILY_SALARY * 0.9)

    # Endgame strategy: Bid higher in the last few days to ensure survival.
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2-3 days
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
        if my_status['hp'] <= 5:
            base_bid = max(base_bid, DAILY_SALARY * 0.95)

    # Final adjustments:
    # Ensure bid is within budget.
    final_bid = min(my_status['budget'], base_bid)
    # Ensure bid is non-negative and at least 1.0 if I need water and can afford it.
    if my_status['hp'] <= 10 and my_status['budget'] > 0: 
        final_bid = max(final_bid, 1.0)
    else: 
        final_bid = max(final_bid, 0.0)
    
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
    num_alive_opponents = len(alive_opponents)
    num_contenders = num_alive_opponents + 1 # Myself + opponents
    available_water = int(day_context['supply']) # CRITICAL INDEX RULE

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid strategy, adjusted by HP and opponent bids
    bid_amount = DAILY_SALARY * 0.55 # Default moderate bid

    # Adjust based on my HP and no_water_days first
    if my_status['hp'] <= 2: # Critical HP
        bid_amount = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP
        bid_amount = DAILY_SALARY * 0.8
    elif my_status['no_water_days'] > 0: # Missed water yesterday
        bid_amount = DAILY_SALARY * 0.75

    # Adjust based on opponent's highest previous bid and supply/demand
    if highest_prev_bid > 0:
        if available_water >= num_contenders: # Abundant supply
            # If healthy, try to bid lower, but still competitive
            if my_status['hp'] > 3:
                bid_amount = min(bid_amount, max(DAILY_SALARY * 0.25, highest_prev_bid * 0.9))
            # If unhealthy, still bid high to secure water, even if abundant
        else: # Scarce supply
            # Need to be aggressive. If current bid_amount is not high enough, raise it.
            bid_amount = max(bid_amount, highest_prev_bid + 2.5)
            # If it's already very high due to low HP, keep it
    else: # No previous bids from opponents, or yesterday_bids was empty
        # If supply is scarce and no previous bids, assume moderate competition
        if available_water < num_contenders:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.65)

    # Ensure bid is at least a minimum positive amount
    bid_amount = max(1.0, bid_amount)

    # Final bid should not exceed budget
    final_bid = min(my_status['budget'], bid_amount)

    return round(final_bid, 2)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQ = 13
    MY_DAILY_SALARY = 150
    EPISODE_DAYS = 10 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], MY_DAILY_SALARY * 0.3)

    bid_target = MY_DAILY_SALARY * 0.5

    if my_status['hp'] <= 2:
        bid_target = MY_DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        bid_target = MY_DAILY_SALARY * 0.8

    if day_context['day'] >= EPISODE_DAYS - 2:
        bid_target = max(bid_target, MY_DAILY_SALARY * 0.9)

    highest_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])

    if highest_prev_bid > 0:
        if highest_prev_bid >= MY_DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                bid_target = min(bid_target, MY_DAILY_SALARY * 0.3)
            else:
                bid_target = max(bid_target, MY_DAILY_SALARY * 0.95)
        else:
            bid_target = max(bid_target, highest_prev_bid + 1.5)

    final_bid = min(my_status['budget'], bid_target)
    return max(1.0, final_bid)
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
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # --- Bidding Strategy ---

    # 1. Survival Bids (High Priority)
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    if my_status['no_water_days'] > 0:
        return min(my_status['budget'], DAILY_SALARY * 0.9)

    # 2. Reactive Bids based on Opponent's Last Day Behavior
    if highest_prev_bid >= DAILY_SALARY * 0.8:
        if my_status['hp'] > 5:
            return min(my_status['budget'], highest_prev_bid + 1, DAILY_SALARY * 0.88)
        else:
            return min(my_status['budget'], highest_prev_bid + 5, DAILY_SALARY * 0.92)

    if highest_prev_bid > DAILY_SALARY * 0.4:
        target_bid = max(DAILY_SALARY * 0.55, highest_prev_bid + 1)
        # If supply is tight and multiple opponents, increase bid slightly
        if current_supply < WATER_REQ * 1.5 and num_alive_opponents > 1:
            target_bid = max(target_bid, DAILY_SALARY * 0.7)
        return min(my_status['budget'], target_bid, DAILY_SALARY * 0.8)

    # 3. Default Bid
    default_bid = DAILY_SALARY * 0.6
    if current_supply < WATER_REQ * 1.5 and num_alive_opponents > 1:
        default_bid = DAILY_SALARY * 0.7

    return min(my_status['budget'], default_bid)
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

    strong_opponent_ids = ['Alex', 'Eric']
    num_strong_opponents_alive = sum(1 for opp_id, opp in opponents_status.items() if opp['alive'] and opp_id in strong_opponent_ids)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    current_bid = DAILY_SALARY * 0.7 # Default competitive bid

    # Adjust bid based on my HP
    if my_status['hp'] <= 2:
        current_bid = DAILY_SALARY * 0.98 # Very aggressive for critical health
    elif my_status['hp'] <= 4:
        current_bid = DAILY_SALARY * 0.90 # Aggressive for low health
    
    # Adjust bid based on highest previous bid from opponents
    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Alex/Eric range
            if my_status['hp'] > 4: # Healthy, try to outbid but cap
                current_bid = max(current_bid, highest_prev_bid + 5)
                current_bid = min(current_bid, DAILY_SALARY * 0.92)
            else: # Unhealthy, must outbid
                current_bid = max(current_bid, highest_prev_bid + 10)
                current_bid = min(current_bid, DAILY_SALARY * 0.99)
        elif highest_prev_bid >= DAILY_SALARY * 0.4: # Moderate bids
            current_bid = max(current_bid, highest_prev_bid + 5)
            current_bid = min(current_bid, DAILY_SALARY * 0.85)
        else: # Low bids (Bob/David range)
            if my_status['hp'] > 4:
                current_bid = DAILY_SALARY * 0.5 # Conservative against weak
            else:
                current_bid = max(current_bid, DAILY_SALARY * 0.7) # Still competitive if unhealthy
    else: # No previous bids or all were 0
        if my_status['hp'] > 4: # Healthy, first day or no strong history
            current_bid = DAILY_SALARY * 0.65
        else: # Unhealthy, first day or no strong history
            current_bid = DAILY_SALARY * 0.85

    # Further adjust based on supply and strong opponents, especially if not already aggressive due to HP
    if my_status['hp'] > 4: # Only if healthy, be more reactive to environment
        if day_context['supply'] <= 18: # Low supply, high competition
            current_bid = max(current_bid, DAILY_SALARY * 0.8)
        if num_strong_opponents_alive >= 1: # At least one strong opponent
            current_bid = max(current_bid, DAILY_SALARY * 0.75)

    final_bid = min(my_status['budget'], current_bid)
    
    # Ensure a minimum bid if budget allows, to stay in contention
    if final_bid < DAILY_SALARY * 0.1 and my_status['budget'] >= DAILY_SALARY * 0.1:
        final_bid = DAILY_SALARY * 0.1

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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid: Start with a moderate bid based on daily salary
    base_bid = DAILY_SALARY * 0.7

    # Aggression based on my current health and water deprivation
    if my_hp <= 2 or my_no_water_days >= 1:
        # Critical state: must get water, bid very aggressively
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4:
        # Low HP: be aggressive to avoid critical state
        base_bid = DAILY_SALARY * 0.85
    elif my_hp > 8 and current_supply >= WATER_REQ * 2:
        # Good HP and abundant supply, can afford to save a bit
        base_bid = DAILY_SALARY * 0.6

    # Adjust for end of episode to ensure survival
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_budget >= DAILY_SALARY * 1.5: # If near end and have sufficient budget
        base_bid = max(base_bid, DAILY_SALARY * 0.9)

    # React to opponents' previous bids
    yesterday_bids = []
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents are bidding high, I need to exceed it to win
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_hp <= 3: # Critical HP, ensure win
                base_bid = max(base_bid, highest_prev_bid + 5)
            else: # Otherwise, slightly outbid
                base_bid = max(base_bid, highest_prev_bid + 1)
        elif highest_prev_bid < DAILY_SALARY * 0.5 and my_hp > 5:
            # If opponents are bidding very low and my HP is good, try to win cheaply
            base_bid = min(base_bid, highest_prev_bid + 1)
        else:
            # Moderate opponent bids, slightly outbid
            base_bid = max(base_bid, highest_prev_bid + 1)

    # Ensure bid does not exceed budget
    final_bid = min(my_budget, base_bid)

    # Ensure a minimum bid to stay competitive, especially if budget is high
    final_bid = max(final_bid, DAILY_SALARY * 0.25)

    return final_bid
"""
