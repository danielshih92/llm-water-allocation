# ============================================================
# Experiment: exp_067
# Agent: Cindy
# Source: exp_067
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    failed_opponents_yesterday = []
    
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            if prev.get('status') == 'no_water':
                failed_opponents_yesterday.append(opp['agent_id'])

    base_bid = DAILY_SALARY * 0.5

    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.75
    elif my_status['no_water_days'] > 0:
        base_bid = DAILY_SALARY * 0.8

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] <= 3:
                base_bid = max(base_bid, highest_prev_bid + 5)
            else:
                base_bid = max(base_bid, highest_prev_bid * 0.9)
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
             base_bid = max(base_bid, highest_prev_bid + 1)
        
        if failed_opponents_yesterday:
            base_bid = max(base_bid, DAILY_SALARY * 0.8)

    current_supply = day_context['supply']
    total_water_demand = WATER_REQ
    for opp in alive_opponents:
        total_water_demand += opp['water_requirement']
    
    if current_supply < total_water_demand * 0.7:
        base_bid *= 1.1
    elif current_supply > total_water_demand * 1.3:
        base_bid *= 0.9

    final_bid = min(my_status['budget'], max(0, base_bid))
    
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0.0

    bid = 0.0
    day_factor = day_context['day'] / EPISODE_DAYS # Scales from 0.1 to 1.0 over the episode

    if my_status['hp'] <= 2: # Critical HP
        bid = DAILY_SALARY * (0.95 + day_factor * 0.05) # Very aggressive, increases with day
    elif my_status['hp'] <= 5: # Low HP
        if max_yesterday_bid > 0:
            bid = max(max_yesterday_bid * 1.05, DAILY_SALARY * 0.8) * (1 + day_factor * 0.05)
        else:
            bid = DAILY_SALARY * (0.8 + day_factor * 0.05)
    elif my_status['hp'] <= 8: # Medium HP
        if max_yesterday_bid > 0:
            bid = max(max_yesterday_bid * 1.02, DAILY_SALARY * 0.65) * (1 + day_factor * 0.02)
        else:
            bid = DAILY_SALARY * (0.65 + day_factor * 0.02)
    else: # High HP
        if max_yesterday_bid > 0:
            bid = max(max_yesterday_bid * 0.98, DAILY_SALARY * 0.55) * (1 + day_factor * 0.01) # Slightly above or below, conservative
        else:
            bid = DAILY_SALARY * (0.55 + day_factor * 0.01)

    bid = max(0.0, bid)
    bid = min(my_status['budget'], bid)

    # If budget is critically low and HP is also critical, bid everything to survive
    if my_status['hp'] <= 2 and my_status['budget'] < DAILY_SALARY * 0.5:
        bid = my_status['budget']

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

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid - start reasonably high given the meta-round context where survivors bid ~120-124
    base_bid = DAILY_SALARY * 0.85 # ~127.5

    # Adjustment for low HP - become very aggressive
    if my_hp <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95 # ~142.5
    elif my_hp <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.90 # ~135

    # Adjustment for remaining days - become more aggressive towards the end
    days_remaining = EPISODE_DAYS - current_day
    if days_remaining <= 2: # Last couple of days, push harder
        base_bid = max(base_bid, DAILY_SALARY * 0.98)
    elif days_remaining <= 4: # Mid-late game
        base_bid = max(base_bid, DAILY_SALARY * 0.92)

    # Adjustment based on opponent's previous bids (yesterday's trace)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were very aggressive, I need to be too.
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            base_bid = max(base_bid, highest_prev_bid + 5.0) # Try to outbid by a small margin
        elif highest_prev_bid >= DAILY_SALARY * 0.7:
            base_bid = max(base_bid, highest_prev_bid + 2.0)

    # Consider supply and number of agents
    # If the number of agents (me + alive opponents) is greater than or equal to the potential water units,
    # competition is fierce.
    total_competitors = num_alive_opponents + 1

    # Check if supply is very tight (e.g., only enough for one agent)
    if supply < 2 * WATER_REQ: 
        base_bid = max(base_bid, DAILY_SALARY * 0.98) # Almost max bid
    # Check if supply is tight for multiple competitors
    elif supply < total_competitors * WATER_REQ and total_competitors > 1:
        base_bid = max(base_bid, DAILY_SALARY * 0.92)

    # Final bid is capped by my budget
    final_bid = min(my_budget, base_bid)

    # Ensure bid is at least 1.0 to avoid bidding 0 and to keep it float
    final_bid = max(1.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.5)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_competitive_bid = DAILY_SALARY * 0.85 
    bid = base_competitive_bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        bid = max(base_competitive_bid, highest_prev_bid + 5.0)
        bid = min(bid, DAILY_SALARY * 1.05) 
    
    if my_status['hp'] <= 3: 
        bid = DAILY_SALARY * 0.99
    elif my_status['hp'] <= 7: 
        bid = max(bid, DAILY_SALARY * 0.9) 
    
    final_bid = min(my_status['budget'], bid)
    
    if my_status['budget'] <= 0:
        return 0.0

    if final_bid < DAILY_SALARY * 0.1 and my_status['budget'] > 0 and my_status['no_water_days'] > 0:
        final_bid = max(final_bid, DAILY_SALARY * 0.1)

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
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimum to win
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1) 

    # Base bid: Start with a solid bid, assuming high competition for 13 water
    bid_amount = DAILY_SALARY * 0.7 # Example: 105.0

    # Collect yesterday's bids and identify Eric
    yesterday_bids = []
    eric_is_only_opponent = False
    eric_prev_bid = 0.0

    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
            if opp_id == "Eric":
                eric_prev_bid = prev.get('bid', 0.0) # Store Eric's previous bid if available

    if num_alive_opponents == 1 and "Eric" in opponents_status and opponents_status["Eric"]['alive']:
        eric_is_only_opponent = True
    
    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Adjust bid based on my HP (desperation)
    if my_status['hp'] <= 0: # Critically low HP, must win
        bid_amount = DAILY_SALARY * 0.95 # Example: 142.5
    elif my_status['hp'] == 1: # Low HP, need to win
        bid_amount = DAILY_SALARY * 0.85 # Example: 127.5
    # If HP is good (>= 2), stick with base_bid or adjust based on opponents

    # Adjust bid based on opponent's previous bids
    if highest_prev_bid > 0:
        if my_status['hp'] > 1: # Healthy HP, try to save but still win
            bid_amount = max(bid_amount, highest_prev_bid + 2.0)
        else: # Desperate HP, outbid aggressively
            bid_amount = max(bid_amount, highest_prev_bid + 5.0)

    # Specific strategy for Eric if he's the only one
    if eric_is_only_opponent:
        # Based on meta-round context, Eric's max_bid was 15.0. He's a cheap competitor.
        # If Eric's previous bid was low, outbid him cheaply.
        # If no previous bid from Eric, assume he's still weak.
        if eric_prev_bid > 0 and eric_prev_bid < DAILY_SALARY * 0.3: # Eric's previous bid was low (e.g., < 45)
            bid_amount = max(bid_amount, eric_prev_bid + 5.0)
            bid_amount = min(bid_amount, DAILY_SALARY * 0.4) # Don't overpay too much against Eric (max 60)
        elif eric_prev_bid == 0: # Eric didn't bid or trace missing, assume low bid capability
            bid_amount = min(bid_amount, DAILY_SALARY * 0.3) # Bid moderately low (max 45)
        # If Eric's bid was somehow high, then treat him like other opponents.
    
    # Final adjustments
    final_bid = min(my_status['budget'], bid_amount)
    final_bid = max(1.0, final_bid) # Minimum bid is 1.0

    # If critically low on HP and budget, bid everything (if > 0)
    if my_status['hp'] <= -1 and my_status['budget'] > 0:
        final_bid = my_status['budget']

    return float(final_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']
    
    days_left = EPISODE_DAYS - current_day + 1

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.05)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    if my_hp <= 2 or my_no_water_days >= 1 or (days_left <= 2 and my_hp < 5):
        emergency_bid = DAILY_SALARY * 1.0 
        
        if highest_prev_bid > DAILY_SALARY * 0.9:
            emergency_bid = max(emergency_bid, highest_prev_bid + 5)
        
        return min(my_budget, emergency_bid)

    HIGH_COMPETITION_THRESHOLD = DAILY_SALARY * 0.85
    MODERATE_COMPETITION_THRESHOLD = DAILY_SALARY * 0.50

    if highest_prev_bid >= HIGH_COMPETITION_THRESHOLD:
        if my_hp > 5:
            bid = min(my_budget, max(DAILY_SALARY * 0.75, highest_prev_bid + 2))
            return min(bid, DAILY_SALARY * 1.05)
        else:
            return min(my_budget, max(DAILY_SALARY * 0.9, highest_prev_bid + 5))
    elif highest_prev_bid >= MODERATE_COMPETITION_THRESHOLD:
        if my_hp > 5:
            return min(my_budget, max(DAILY_SALARY * 0.6, highest_prev_bid + 1))
        else:
            return min(my_budget, max(DAILY_SALARY * 0.75, highest_prev_bid + 5))
    else:
        return min(my_budget, DAILY_SALARY * 0.6)

    return min(my_budget, DAILY_SALARY * 0.7)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta_round_state

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    # Identify alive opponents and count them
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)
    num_total_active_agents = num_alive_opponents + 1 # Myself + opponents

    # Base bid strategy: a moderate bid to stay in the game
    bid = DAILY_SALARY * 0.6

    # --- Desperation Logic (HP based) ---
    # If HP is very low, bid very aggressively to survive
    if my_hp <= 2:
        bid = max(bid, DAILY_SALARY * 0.95)
    # If HP is low, bid aggressively
    elif my_hp <= 4:
        bid = max(bid, DAILY_SALARY * 0.85)

    # --- Competition Logic (Alex specific) ---
    alex_status = opponents_status.get('Alex')
    alex_alive = alex_status and alex_status['alive']
    alex_prev_bid = 0
    if alex_alive:
        alex_prev_trace = alex_status.get('previous_trace', {})
        if alex_prev_trace and alex_prev_trace.get('bid') is not None:
            alex_prev_bid = alex_prev_trace['bid']

    # If Alex is alive and historically strong, react to his previous bid
    if alex_alive:
        # If Alex bid high, try to outbid him by a small margin
        if alex_prev_bid > DAILY_SALARY * 0.7:
            bid = max(bid, alex_prev_bid + 5)
        # If Alex bid moderately, slightly outbid him
        elif alex_prev_bid > DAILY_SALARY * 0.3:
            bid = max(bid, alex_prev_bid + 1)
        # If Alex bid low or 0, maintain a strong presence
        else:
            bid = max(bid, DAILY_SALARY * 0.65) # Ensure I get water over weaker players

    # --- Supply and Demand Logic ---
    # Supply is 15-25, my WATER_REQ is 13. This means there's always enough for one,
    # but never enough for two agents to get their full 13 units. Priority is key.
    
    # If current_supply is tight (e.g., less than 1.5 times my requirement) and multiple agents are active,
    # competition is higher, so increase bid.
    if current_supply < WATER_REQ * 1.5 and num_total_active_agents > 1: # Supply 15-19
        bid = max(bid, DAILY_SALARY * 0.75)

    # --- End Game Logic ---
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_hp > 0: # Last few days, push to survive
        bid = max(bid, DAILY_SALARY * 0.8)
    elif remaining_days <= 4 and my_hp > 0 and my_budget > DAILY_SALARY * 2: # Mid-late game, if budget allows
        bid = max(bid, DAILY_SALARY * 0.7)

    # --- Final Bid Adjustments ---
    # Ensure bid does not exceed current budget
    bid = min(bid, my_budget)

    # Ensure bid is at least 0.1 to participate if budget allows, else 0
    bid = max(0.1, bid) if my_budget > 0 else 0.0

    return bid
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

    base_bid = 0.0
    if my_status['hp'] <= 1:
        base_bid = DAILY_SALARY * 0.98
    elif my_status['hp'] <= 3:
        base_bid = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 5:
        base_bid = DAILY_SALARY * 0.75
    else:
        base_bid = DAILY_SALARY * 0.5

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if my_status['hp'] <= 3:
            base_bid = max(base_bid, highest_prev_bid + 5)
        elif my_status['hp'] <= 5:
            base_bid = max(base_bid, highest_prev_bid + 2)
        else:
            if highest_prev_bid >= DAILY_SALARY * 0.9:
                base_bid = max(base_bid, DAILY_SALARY * 0.6)
            else:
                base_bid = max(base_bid, highest_prev_bid + 1)
    
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2:
        if my_status['hp'] <= 5:
            base_bid = max(base_bid, DAILY_SALARY * 0.95)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.8)
    elif remaining_days <= 4 and my_status['hp'] <= 3:
        base_bid = max(base_bid, DAILY_SALARY * 0.92)

    final_bid = min(my_status['budget'], base_bid)
    final_bid = max(0.0, final_bid)

    return float(final_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_active_players = len(alive_opponents) + 1 # Me + opponents

    # Determine base bid based on urgency (my HP)
    if my_status['hp'] <= 2: # Critical
        my_urgency_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5: # Low
        my_urgency_bid = DAILY_SALARY * 0.75
    else: # Healthy
        my_urgency_bid = DAILY_SALARY * 0.55 # Default healthy bid

    # Check competition from supply
    max_full_allocations = int(day_context['supply'] // WATER_REQ)
    is_supply_tight = num_active_players > max_full_allocations

    # Collect yesterday's bids from previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    strategic_bid = my_urgency_bid # Start with bid based on my urgency

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # React to opponent's previous aggression
        if is_supply_tight or my_status['hp'] <= 5: # If competition is high or I need water
            if max_prev_bid >= DAILY_SALARY * 0.8: # Very aggressive opponents
                strategic_bid = max(strategic_bid, max_prev_bid + 5) # Try to outbid them
            elif max_prev_bid >= DAILY_SALARY * 0.5: # Moderately aggressive
                strategic_bid = max(strategic_bid, avg_prev_bid * 1.1) # Beat average
            else: # Low aggression, but still need to win if supply is tight
                strategic_bid = max(strategic_bid, avg_prev_bid * 1.2) # Beat average, but not too high
        else: # Supply is not tight, and I'm healthy - can save money
            strategic_bid = max(strategic_bid, avg_prev_bid * 0.9) # Bid below average, try to get cheap water
            # But ensure it's at least a reasonable amount to win if others are bidding low
            strategic_bid = max(strategic_bid, DAILY_SALARY * 0.3) # Minimum bid if not urgent

    # If no opponents, or all opponents are dead, bid minimally unless critical HP
    if not alive_opponents:
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.8) # Still need water, but no competition
        return min(my_status['budget'], DAILY_SALARY * 0.1) # Very low bid to save money

    # Final bid adjustment
    final_bid = min(my_status['budget'], strategic_bid)
    final_bid = max(0.0, final_bid) # Ensure non-negative bid

    return final_bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.55

    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.98
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.85
    elif my_status['hp'] <= 6:
        base_bid = DAILY_SALARY * 0.7

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 4:
                bid = max(base_bid, highest_prev_bid + 1)
                bid = min(bid, DAILY_SALARY * 0.95)
            else:
                bid = max(base_bid, highest_prev_bid + 5)
                bid = min(bid, DAILY_SALARY * 0.99)
        else:
            bid = max(base_bid, highest_prev_bid + 2)
            bid = min(bid, DAILY_SALARY * 0.78)
    else:
        bid = base_bid

    final_bid = max(1.0, min(bid, my_status['budget']))
    
    return final_bid
"""
