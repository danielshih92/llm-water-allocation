# ============================================================
# Experiment: exp_039
# Agent: Cindy
# Source: exp_039
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    CRITICAL_HP_THRESHOLD = 2
    MODERATE_HP_THRESHOLD = 4

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to get water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Calculate total water demand (including myself)
    total_water_demand = WATER_REQ
    for opp in alive_opponents:
        total_water_demand += opp['water_requirement']

    # --- Bidding Logic ---

    # 1. Desperation Mode (Critical HP)
    if my_status['hp'] <= CRITICAL_HP_THRESHOLD:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # 2. Supply is very abundant - enough for everyone to get their full requirement
    if day_context['supply'] >= total_water_demand:
        bid = DAILY_SALARY * 0.4 # Base bid for abundant supply
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            if highest_prev_bid > DAILY_SALARY * 0.5:
                bid = max(bid, highest_prev_bid * 0.9) # Slightly less than highest if it was high
            else:
                bid = max(bid, highest_prev_bid + 1) # Just slightly above if it was low
        return min(my_status['budget'], bid)

    # 3. Moderate HP or Scarce/Normal Supply
    current_bid = DAILY_SALARY * 0.55 # Default bid for normal conditions

    # Adjust based on yesterday's bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.8:
            current_bid = DAILY_SALARY * 0.8 # Bid high to compete
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            current_bid = max(current_bid, highest_prev_bid * 1.05) # Try to slightly outbid
        else:
            current_bid = max(current_bid, avg_prev_bid + 2) # Bid slightly above average

    # Adjust for my HP if moderately low (not critical, but needs attention)
    if my_status['hp'] <= MODERATE_HP_THRESHOLD and my_status['hp'] > CRITICAL_HP_THRESHOLD:
        current_bid = max(current_bid, DAILY_SALARY * 0.7)

    # Ensure bid is at least a reasonable amount to secure water (e.g., cost of ~1 unit water)
    min_effective_bid_floor = DAILY_SALARY / WATER_REQ * 1.5
    current_bid = max(current_bid, min_effective_bid_floor)

    # Cap the bid at a reasonable maximum unless in critical state
    current_bid = min(current_bid, DAILY_SALARY * 0.9)

    return min(my_status['budget'], current_bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    # Base bid, starting strong due to high competition
    bid = DAILY_SALARY * 0.8 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Adjust bid based on my HP
    if my_status['hp'] <= 3: # Critical HP: bid very high
        bid = DAILY_SALARY * 0.95 
    elif my_status['hp'] >= 8: # Comfortable HP: can be slightly less aggressive, but still competitive
        bid = DAILY_SALARY * 0.75 
    
    # Adjust bid based on opponents' previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were very aggressive, I need to match or exceed.
        if highest_prev_bid >= DAILY_SALARY * 0.9: # Opponents bid very high
            if my_status['hp'] <= 5: # If my HP is not great, I must fight harder
                bid = max(bid, highest_prev_bid + 5.0) # Outbid by a decent margin
            else: # If my HP is good, still try to win but less desperately
                bid = max(bid, highest_prev_bid + 1.0) # Outbid by a small margin
        elif highest_prev_bid >= DAILY_SALARY * 0.7: # Opponents bid moderately high
            bid = max(bid, highest_prev_bid + 2.0) # Try to win by a small margin
        else: # Opponents bid low, ensure I still bid competitively
            bid = max(bid, DAILY_SALARY * 0.6) 
    else: # No previous bids from opponents (e.g., first day or all opponents died/no trace)
        # Default strong bid if no previous opponent data to establish presence
        bid = DAILY_SALARY * 0.85 

    # Ensure bid does not exceed current budget
    bid = min(bid, my_status['budget'])
    
    # Ensure bid is at least 0
    bid = max(0.0, bid)

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
    num_alive_opponents = len(alive_opponents)

    # Scenario 1: No opponents left, bid minimum to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    yesterday_bids = []
    eric_yesterday_bid = 0.0
    eric_is_alive = False

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            if opp['agent_id'] == "Eric":
                eric_yesterday_bid = prev['bid']
                eric_is_alive = True

    # Scenario 2: Yesterday's bids are available
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # Aggressive reaction if Eric bid very high, or general highest bid is very high
        if (eric_is_alive and eric_yesterday_bid >= DAILY_SALARY * 0.8) or \
           (highest_prev_bid >= DAILY_SALARY * 0.85):
            # If I'm low on HP or missed water, bid very aggressively
            if my_status['hp'] <= 3 or my_status['no_water_days'] > 0:
                return min(my_status['budget'], DAILY_SALARY * 0.95)
            # If HP is good, but competition is fierce, still bid high to stay competitive
            bid_amount = DAILY_SALARY * 0.75 # A strong bid, but not desperate

        # Moderate reaction: bid slightly above the highest yesterday's bid
        else:
            bid_amount = max(DAILY_SALARY * 0.5, highest_prev_bid + 5.0) # Add a buffer to win
        
        # If my HP is low, be more aggressive
        if my_status['hp'] <= 5 or my_status['no_water_days'] > 0:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.7)

        # Consider supply: if supply is high, maybe don't bid excessively
        # Calculate how many players can get water
        num_slots = int(day_context['supply'] / WATER_REQ)
        if num_slots >= (num_alive_opponents + 1): # Enough for everyone
            # If supply is plentiful, try to be more conservative if HP is good
            if my_status['hp'] > 5 and my_status['no_water_days'] == 0:
                bid_amount = min(bid_amount, DAILY_SALARY * 0.6)
            else: # Still be competitive if HP is not great
                bid_amount = min(bid_amount, DAILY_SALARY * 0.75)
        elif num_slots < (num_alive_opponents + 1) and num_slots >= 1: # Scarcity
            # Increase bid aggressiveness slightly if water is tight
            if my_status['hp'] <= 5 or my_status['no_water_days'] > 0:
                 bid_amount = max(bid_amount, DAILY_SALARY * 0.8) # Push harder
            else:
                 bid_amount = max(bid_amount, DAILY_SALARY * 0.65) # Stay competitive
        else: # Extreme scarcity (< WATER_REQ available) - very high competition
            bid_amount = max(bid_amount, DAILY_SALARY * 0.9)

        return min(my_status['budget'], bid_amount)

    # Scenario 3: No yesterday's bids (e.g., Day 1 or all opponents didn't bid)
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        return min(my_status['budget'], DAILY_SALARY * 0.9) # Desperate bid
    
    # Default bid for Day 1 or when no previous bids are available
    # Adjust based on number of opponents
    if num_alive_opponents >= 3: # Many active opponents
        return min(my_status['budget'], DAILY_SALARY * 0.6)
    elif num_alive_opponents >= 1: # Few active opponents
        return min(my_status['budget'], DAILY_SALARY * 0.5)
    
    # Fallback, should be covered by 'not alive_opponents' but for safety
    return min(my_status['budget'], DAILY_SALARY * 0.4)
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
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    base_bid = DAILY_SALARY * 0.55

    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] <= 6:
        base_bid = DAILY_SALARY * 0.7

    if my_status['no_water_days'] > 0:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)

    if day_context['day'] == EPISODE_DAYS:
        if my_status['hp'] < EPISODE_DAYS:
            return my_status['budget']
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.2)

    yesterday_opponent_bids = []
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                yesterday_opponent_bids.append(prev_trace['bid'])

    if yesterday_opponent_bids:
        highest_prev_bid = max(yesterday_opponent_bids)
        
        if my_status['hp'] <= 4:
            base_bid = max(base_bid, highest_prev_bid + 5)
        elif my_status['hp'] <= 6:
            base_bid = max(base_bid, highest_prev_bid + 3)
        else:
            current_supply = day_context['supply']
            if current_supply < WATER_REQ * 1.5 and highest_prev_bid > DAILY_SALARY * 0.8:
                base_bid = max(base_bid, DAILY_SALARY * 0.6)
            else:
                base_bid = max(base_bid, highest_prev_bid + 1.5)

    final_bid = min(my_status['budget'], base_bid)
    final_bid = max(1.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid minimally to conserve budget and ensure water if available.
    if not alive_opponents:
        return min(my_status['budget'], 1)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid strategy: Start with a moderate bid, adjusted by supply.
    base_bid = DAILY_SALARY * 0.6 # A reasonable starting point (90)

    # Adjust base bid based on supply: lower supply means higher competition.
    if day_context['supply'] < 18.0: # If supply is low (e.g., 15, 16, 17)
        base_bid *= 1.1
    elif day_context['supply'] > 22.0: # If supply is high (e.g., 23, 24, 25)
        base_bid *= 0.9

    current_bid = base_bid

    # Adjust bid based on opponent's highest bid from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were bidding very high yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.85: # e.g., 127.5
            # If my HP is low, bid aggressively to survive
            if my_status['hp'] <= 3:
                current_bid = DAILY_SALARY * 0.95 # Maximize chance of winning (142.5)
            # If my HP is good, try to be competitive but avoid overspending too much
            else:
                current_bid = max(base_bid, highest_prev_bid * 0.9) # Stay close but slightly cautious
        # If opponents were bidding moderately
        else:
            current_bid = max(base_bid, highest_prev_bid + 5) # Slightly outbid to win

    # Final adjustment for my own desperation (overrides previous logic if critical)
    if my_status['hp'] <= 2:
        current_bid = DAILY_SALARY * 0.98 # Extreme desperation (147)
    elif my_status['hp'] <= 4 and my_status['no_water_days'] > 0:
        current_bid = DAILY_SALARY * 0.9 # High desperation (135)

    # Ensure bid does not exceed available budget
    return min(my_status['budget'], current_bid)
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

    # If no opponents, bid minimal to save budget
    if not alive_opponents:
        return max(1.0, min(my_status['budget'], DAILY_SALARY * 0.1))

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Default bid if no previous bids or for general healthy state
    # This is a moderate bid to stay competitive given the severe water shortage (supply 15-25, req 13).
    current_bid = DAILY_SALARY * 0.55 # ~82.5

    # Adjust bid based on opponent's highest previous bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were bidding very high (e.g., Eric's historical bids), respond aggressively
        if highest_prev_bid >= DAILY_SALARY * 0.85: # ~127.5
            current_bid = max(current_bid, highest_prev_bid + 3.0) # Try to outbid significantly
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # ~90
            current_bid = max(current_bid, highest_prev_bid + 1.5) # Try to outbid moderately
        else:
            # Lower pressure, try to win cheaply but still ensure a win
            current_bid = max(current_bid, highest_prev_bid + 0.5)

    # Overwrite bid if my HP is critical, prioritizing survival above all else
    if my_status['hp'] <= 2: # Very critical, bid almost maximum
        current_bid = DAILY_SALARY * 0.98 # ~147
    elif my_status['hp'] <= 5: # Low health, bid very high
        current_bid = DAILY_SALARY * 0.90 # ~135
    
    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], current_bid)
    
    # Ensure a minimum bid if budget allows, to stay in contention
    if final_bid < 1.0 and my_status['budget'] > 0:
        final_bid = 1.0 # Bid at least 1 to try and get water

    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid conservatively to save budget.
    if not alive_opponents:
        return max(0.01, min(my_budget, DAILY_SALARY * 0.4))

    # Collect yesterday's bids from all active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Decision logic based on yesterday's highest pressure and my health
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If opponents were very aggressive yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If I'm healthy (good HP and no recent water deprivation), try to conserve
            if my_hp > 3 and my_no_water_days == 0:
                return max(0.01, min(my_budget, DAILY_SALARY * 0.3))
            # Otherwise, I need water, so bid aggressively to survive
            return max(0.01, min(my_budget, DAILY_SALARY * 0.95))
        
        # If opponents were moderately aggressive or less
        # Bid slightly above the highest previous bid, or a solid moderate amount
        # Ensure it's at least 50% of salary to be competitive
        return max(0.01, min(my_budget, max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)))

    # If no previous bids are available (e.g., first day or opponents didn't bid)
    # Base strategy on my current health
    if my_hp <= 2 or my_no_water_days >= 1: # Critical health or deprived of water
        return max(0.01, min(my_budget, DAILY_SALARY * 0.9)) # Bid high to survive
    
    # Otherwise, I'm relatively healthy, bid moderately
    return max(0.01, min(my_budget, DAILY_SALARY * 0.55))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.5

    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.85
    elif my_status['hp'] <= 6:
        base_bid = DAILY_SALARY * 0.7

    potential_recipients = int(day_context['supply'] // WATER_REQ)

    if potential_recipients == 1:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif potential_recipients == 2 and len(alive_opponents) >= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.75)
    else:
        base_bid = max(base_bid, DAILY_SALARY * 0.4)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if my_status['hp'] > 6:
            if highest_prev_bid >= DAILY_SALARY * 0.8:
                base_bid = max(base_bid, highest_prev_bid + 5)
            elif highest_prev_bid >= DAILY_SALARY * 0.6:
                base_bid = max(base_bid, highest_prev_bid + 2)
            else:
                base_bid = min(base_bid, highest_prev_bid + 1)
        else:
            base_bid = max(base_bid, highest_prev_bid + 5)

    if day_context['day'] >= EPISODE_DAYS - 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.99)
    elif day_context['day'] >= EPISODE_DAYS - 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    final_bid = max(0.0, min(my_status['budget'], base_bid))

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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']

    alex_prev_bid = 0.0
    bob_prev_bid = 0.0

    alive_opponents = []
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            alive_opponents.append(opp_data)
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                if opp_id == "Alex":
                    alex_prev_bid = prev['bid']
                elif opp_id == "Bob":
                    bob_prev_bid = prev['bid']

    if len(alive_opponents) <= 1: 
        return min(my_budget, DAILY_SALARY * 0.4)

    base_bid = DAILY_SALARY * 0.6 

    if alex_prev_bid > 0:
        if alex_prev_bid >= DAILY_SALARY * 0.8: 
            base_bid = max(base_bid, alex_prev_bid + 5.0)
        elif alex_prev_bid >= DAILY_SALARY * 0.5: 
            base_bid = max(base_bid, alex_prev_bid + 2.0)
    
    if bob_prev_bid > 0:
        if bob_prev_bid >= DAILY_SALARY * 0.4: 
             base_bid = max(base_bid, bob_prev_bid + 1.0)

    if my_hp <= 2: 
        base_bid = max(base_bid, DAILY_SALARY * 1.05) 
    elif my_hp <= 4: 
        base_bid = max(base_bid, DAILY_SALARY * 0.9) 
    elif my_hp <= 6: 
        base_bid = max(base_bid, DAILY_SALARY * 0.75) 

    days_left = EPISODE_DAYS - current_day
    if days_left <= 2: 
        base_bid = max(base_bid, DAILY_SALARY * 1.1) 
    elif days_left <= 4: 
        base_bid = max(base_bid, DAILY_SALARY * 0.95) 

    final_bid = min(my_budget, base_bid)

    if final_bid <= 0.0 and my_budget > 0.0 and my_hp < 10: 
        final_bid = min(my_budget, DAILY_SALARY * 0.1) 

    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid conservatively to ensure survival without overspending.
    if not alive_opponents:
        # Ensure we don't bid more than our current budget
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Decision logic based on yesterday's highest pressure and my current health
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If opponents were bidding very high yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If I'm relatively healthy, I can afford to save money and let opponents overspend.
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            # If I'm not healthy, I need water despite high competition.
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        
        # If opponents were not excessively aggressive, bid slightly higher than the highest previous bid,
        # ensuring a minimum competitive bid.
        return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
    
    # Fallback strategy if no yesterday bids are available (e.g., first day or opponents didn't bid)
    # Prioritize survival if health is low.
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    # Otherwise, bid moderately to conserve budget while still aiming for water.
    return min(my_status['budget'], DAILY_SALARY * 0.55)
"""
