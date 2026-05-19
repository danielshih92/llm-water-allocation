# ============================================================
# Experiment: exp_104
# Agent: Cindy
# Source: exp_104
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # --- Determine my base bid ---
    # Start with a moderate bid
    bid = DAILY_SALARY * 0.55

    # --- Survival logic: increase bid if desperate ---
    if my_status['hp'] <= 1:
        # Critical HP, bid very aggressively
        bid = DAILY_SALARY * 0.98
    elif my_status['hp'] <= 2:
        # Low HP, bid aggressively
        bid = DAILY_SALARY * 0.85
    elif my_status['no_water_days'] >= 1:
        # Went without water yesterday, need it today
        bid = max(bid, DAILY_SALARY * 0.7)

    # --- Supply-demand adjustment ---
    current_supply = day_context['supply']
    # Estimate total water needed by all active players
    # Assuming everyone needs WATER_REQ
    total_potential_demand = WATER_REQ * (num_alive_opponents + 1)

    if current_supply < WATER_REQ * (num_alive_opponents + 1):
        # Supply is less than total demand, competition will be high
        bid = max(bid, DAILY_SALARY * 0.7)
        if current_supply < WATER_REQ: # Not even enough for one person
            bid = max(bid, DAILY_SALARY * 0.9) # Bid very high
    elif current_supply >= WATER_REQ * (num_alive_opponents + 2):
        # Supply is abundant, can try to conserve
        bid = min(bid, DAILY_SALARY * 0.4)

    # --- Opponent reaction logic (based on previous_trace) ---
    max_opp_bid_yesterday = 0
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                max_opp_bid_yesterday = max(max_opp_bid_yesterday, prev_trace['bid'])

    if max_opp_bid_yesterday > 0:
        # If opponents bid high yesterday, and I need water or supply is tight,
        # consider bidding slightly higher than their max to secure water.
        if (my_status['hp'] <= 3 or my_status['no_water_days'] >= 1 or
            current_supply < total_potential_demand):
            bid = max(bid, max_opp_bid_yesterday + 1.0)
        else:
            # If not desperate, but opponents are aggressive, just ensure we're competitive
            bid = max(bid, max_opp_bid_yesterday * 0.9)

    # --- Final checks ---
    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], bid)
    # Ensure bid is not negative
    final_bid = max(0.0, final_bid)

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

    base_bid = DAILY_SALARY * 0.55 

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.8: 
            base_bid = max(base_bid, highest_prev_bid + 5.0) 
        elif highest_prev_bid >= DAILY_SALARY * 0.6: 
            base_bid = max(base_bid, highest_prev_bid + 1.0) 
        else: 
            base_bid = max(base_bid, highest_prev_bid * 1.1)

    if my_status['hp'] <= 3:
        base_bid = max(base_bid, DAILY_SALARY * 0.95) 
    elif my_status['hp'] <= 5:
        base_bid = max(base_bid, DAILY_SALARY * 0.8) 

    current_day = day_context['day']
    if current_day > EPISODE_DAYS * 0.7: 
        base_bid = max(base_bid, DAILY_SALARY * 0.75) 
    elif current_day > EPISODE_DAYS * 0.5: 
        base_bid = max(base_bid, DAILY_SALARY * 0.65) 

    final_bid = min(my_status['budget'], base_bid)
    
    if alive_opponents and final_bid < DAILY_SALARY * 0.1: 
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.1) 

    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid low but ensure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Desperation mode: If HP is very low, bid aggressively to survive
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # If there were previous bids, react to the highest
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If yesterday's highest bid was very high (indicating strong competition)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If my HP is still good, I can be slightly less aggressive but still competitive
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.7)
            # If my HP is getting low, I need to be aggressive to secure water
            return min(my_status['budget'], DAILY_SALARY * 0.9)

        # If yesterday's highest bid was moderate, try to outbid slightly
        return min(my_status['budget'], max(DAILY_SALARY * 0.65, highest_prev_bid + 2.5))

    # Fallback if no yesterday bids (e.g., first day of meta-round)
    # Bid a solid amount to secure water without overspending
    return min(my_status['budget'], DAILY_SALARY * 0.75)
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
        return min(my_status['budget'], 1.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    my_bid = 0.0

    if my_status['hp'] <= 2:
        my_bid = max(highest_prev_bid * 1.05 + 5, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4:
        my_bid = max(highest_prev_bid * 1.03 + 3, DAILY_SALARY * 0.85)
    else:
        my_bid = max(highest_prev_bid * 1.01 + 1, DAILY_SALARY * 0.75)
        
        remaining_days = EPISODE_DAYS - day_context['day'] + 1
        if remaining_days <= 3 and my_status['budget'] > DAILY_SALARY * 2:
             my_bid = max(my_bid, DAILY_SALARY * 0.9)

    my_bid = min(my_status['budget'], my_bid)
    
    if my_bid < 1.0 and my_status['budget'] >= 1.0:
        my_bid = 1.0

    if my_status['budget'] <= 0:
        return 0.0

    return my_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    current_day = day_context['day']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    my_urgency_score = 0
    if my_status['no_water_days'] > 0:
        my_urgency_score += 2
    if my_status['hp'] <= 2:
        my_urgency_score += 3
    elif my_status['hp'] <= 4:
        my_urgency_score += 1

    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2:
        my_urgency_score += 2

    yesterday_bids = []
    opponent_urgency_scores = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

            opp_urgency = 0
            if opp['no_water_days'] > 0:
                opp_urgency += 2
            if opp['hp'] <= 2:
                opp_urgency += 3
            elif opp['hp'] <= 4:
                opp_urgency += 1
            if remaining_days <= 2:
                opp_urgency += 2
            opponent_urgency_scores.append(opp_urgency)

    max_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    base_bid = DAILY_SALARY * 0.5
    bid = base_bid

    if my_urgency_score >= 3:
        bid = DAILY_SALARY * 0.95
        if remaining_days <= 2 and my_status['budget'] > bid:
             bid = min(my_status['budget'], DAILY_SALARY * 1.1)
        else:
             bid = min(my_status['budget'], bid)
        
        if max_yesterday_bid > base_bid * 1.2:
            bid = max(bid, max_yesterday_bid + 5)

    elif my_urgency_score >= 1:
        bid = DAILY_SALARY * 0.7
        if max_yesterday_bid > base_bid:
            bid = max(bid, max_yesterday_bid + 1)
    else:
        if max_yesterday_bid > 0 and max_yesterday_bid < base_bid * 0.8:
            bid = max(DAILY_SALARY * 0.4, max_yesterday_bid + 1)
        elif max_yesterday_bid >= base_bid * 0.8:
            bid = max(bid, max_yesterday_bid + 1)

    final_bid = min(my_status['budget'], bid)

    if my_status['hp'] > 7 and my_status['budget'] > DAILY_SALARY * 5 and num_alive_opponents > 0:
        avg_opp_urgency = sum(opponent_urgency_scores) / num_alive_opponents if num_alive_opponents > 0 else 0
        if avg_opp_urgency < 2 and max_yesterday_bid < DAILY_SALARY * 0.6:
            final_bid = min(final_bid, DAILY_SALARY * 0.55)

    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    supply = day_context['supply']
    day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid - default moderate bid
    base_bid = DAILY_SALARY * 0.5

    # If no opponents left, bid minimally to secure water
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = 0.0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    # Strategy based on my HP and yesterday's bids
    bid_amount = base_bid # Start with base

    if my_hp <= 2: # Critical HP: Bid aggressively
        bid_amount = max(bid_amount * 1.8, max_yesterday_bid * 1.1 + 10)
        bid_amount = max(bid_amount, DAILY_SALARY * 0.9) # Ensure it's high
    elif my_hp <= 4: # Low HP: Bid strongly
        bid_amount = max(bid_amount * 1.4, max_yesterday_bid * 1.05 + 5)
        bid_amount = max(bid_amount, DAILY_SALARY * 0.75)
    elif my_no_water_days > 0: # Missed water yesterday, need to win
        bid_amount = max(bid_amount * 1.5, max_yesterday_bid * 1.1 + 10)
        bid_amount = max(bid_amount, DAILY_SALARY * 0.8)
    else: # Healthy HP: Adjust based on competition and supply
        # If max yesterday bid was high, assume competition is high
        if max_yesterday_bid > DAILY_SALARY * 0.7:
            bid_amount = max(bid_amount * 1.1, max_yesterday_bid * 1.02 + 2)
            bid_amount = max(bid_amount, DAILY_SALARY * 0.6)
        # If max yesterday bid was moderate or low, try to save
        else:
            bid_amount = max(bid_amount * 0.8, max_yesterday_bid * 0.9 + 1)
            bid_amount = min(bid_amount, DAILY_SALARY * 0.55) # Cap it to save budget

    # Adjust bid based on supply scarcity
    # Calculate how many water units are needed for all alive agents including myself
    total_water_units_needed = (num_alive_opponents + 1) * WATER_REQ

    if supply < total_water_units_needed: # Supply is scarce
        # Increase bid to reflect higher competition
        bid_amount = bid_amount * 1.15
        if my_hp < 5: # If also low on HP, be very aggressive
            bid_amount = bid_amount * 1.2
    elif supply >= total_water_units_needed + WATER_REQ * num_alive_opponents: # Supply is very abundant
        # Decrease bid if we can afford to
        bid_amount = bid_amount * 0.8
        
    # End-game strategy: If it's the last day or second to last, be more aggressive if needed
    remaining_days = EPISODE_DAYS - day
    if remaining_days <= 1: # Last day
        bid_amount = max(bid_amount, DAILY_SALARY * 0.95) # Go all in to survive
    elif remaining_days == 2 and my_hp < 5: # Second to last day, low HP
        bid_amount = max(bid_amount, DAILY_SALARY * 0.85)

    # Ensure bid is within budget and not negative. Always bid at least 1.0.
    final_bid = max(1.0, min(my_budget, bid_amount))

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

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Base bid, adjusted by HP
    base_bid = DAILY_SALARY * 0.5
    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5:
        base_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] <= 7:
        base_bid = DAILY_SALARY * 0.7

    # Look at yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest bid was very high, we might need to exceed it
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] <= 3:
                base_bid = max(base_bid, highest_prev_bid + 5.0)
            else:
                base_bid = max(base_bid, highest_prev_bid * 0.95)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            base_bid = max(base_bid, highest_prev_bid + 1.0)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.4)

    # Adjust for remaining days
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2:
        if my_status['hp'] <= 5:
            base_bid = max(base_bid, DAILY_SALARY * 0.9)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.6)
    elif day_context['day'] <= 3:
        if my_status['hp'] <= 3:
            base_bid = max(base_bid, DAILY_SALARY * 0.85)

    final_bid = min(my_status['budget'], base_bid)
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

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0
    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0

    base_bid = DAILY_SALARY * 0.5 

    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.8
    elif my_status['no_water_days'] > 0:
        base_bid = DAILY_SALARY * 0.85

    if day_context['supply'] < 2 * WATER_REQ and num_alive_opponents > 1:
        if my_status['hp'] <= 4:
            base_bid = max(base_bid, DAILY_SALARY * 0.95)
        else:
            base_bid = max(base_bid, max_yesterday_bid * 1.05 if max_yesterday_bid else DAILY_SALARY * 0.7)
    elif day_context['supply'] >= 2 * WATER_REQ and num_alive_opponents > 1:
        if my_status['hp'] > 5:
            base_bid = min(base_bid, DAILY_SALARY * 0.6)
        else:
            base_bid = max(base_bid, avg_yesterday_bid * 1.1 if avg_yesterday_bid else DAILY_SALARY * 0.65)

    if max_yesterday_bid > DAILY_SALARY * 0.7:
        base_bid = max(base_bid, max_yesterday_bid + (DAILY_SALARY * 0.05))

    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 3 and my_status['budget'] > DAILY_SALARY * 5:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)

    final_bid = min(my_status['budget'], base_bid)

    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQ = 13
    MY_DAILY_SALARY = 150
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents are alive, bid conservatively to save budget
    if not alive_opponents:
        return min(my_status['budget'], MY_DAILY_SALARY * 0.4)

    bid_amount = MY_DAILY_SALARY * 0.55 # Default moderate bid

    # Priority 1: Last day, must survive
    if day_context['day'] == EPISODE_DAYS:
        bid_amount = MY_DAILY_SALARY * 0.95
    # Priority 2: Critically low HP, must survive
    elif my_status['hp'] <= 2:
        bid_amount = MY_DAILY_SALARY * 0.9
    # Priority 3: React to yesterday's bids
    elif yesterday_bids := [opp.get('previous_trace', {}).get('bid') for opp in alive_opponents if opp.get('previous_trace', {}).get('bid') is not None]:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= MY_DAILY_SALARY * 0.85: # High bids yesterday, indicating high competition
            if my_status['hp'] > 3: # My HP is good, can afford to be conservative
                bid_amount = MY_DAILY_SALARY * 0.3
            else: # My HP is low, must respond aggressively
                bid_amount = MY_DAILY_SALARY * 0.95
        else: # Moderate bids yesterday
            # Bid slightly above highest previous bid, or a moderate base
            bid_amount = max(MY_DAILY_SALARY * 0.5, highest_prev_bid + 1.5)
    # Else (no previous bids, e.g., first day, and not last day/low HP), use default moderate bid_amount
    
    # Ensure bid does not exceed current budget
    return min(my_status['budget'], bid_amount)
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
    
    total_water_demand = WATER_REQ
    for opp in alive_opponents:
        total_water_demand += opp['water_requirement']

    scarcity_multiplier = 1.0
    if day_context['supply'] < total_water_demand:
        scarcity_multiplier = 1.0 + (total_water_demand - day_context['supply']) / total_water_demand
    elif day_context['supply'] > total_water_demand:
        scarcity_multiplier = max(0.9, 1.0 - (day_context['supply'] - total_water_demand) / day_context['supply'])
    
    base_bid = DAILY_SALARY * 0.5

    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5:
        base_bid = DAILY_SALARY * 0.75
    
    current_bid = base_bid

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 3:
                current_bid = max(base_bid, highest_prev_bid * 0.9) 
            else:
                current_bid = max(base_bid, highest_prev_bid * 1.05) 
        else:
            current_bid = max(base_bid, highest_prev_bid + 5.0) 
    
    current_bid = current_bid * scarcity_multiplier

    final_bid = min(my_status['budget'], max(1.0, current_bid))
    
    return final_bid
"""
