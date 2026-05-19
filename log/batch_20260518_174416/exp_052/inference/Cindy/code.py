# ============================================================
# Experiment: exp_052
# Agent: Cindy
# Source: exp_052
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

    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    bid_amount = 0.0

    # Determine a base bid based on my HP
    if my_hp <= 2: # Critical HP: must win
        bid_amount = DAILY_SALARY * 0.98
    elif my_hp <= 4: # Low HP: bid very strongly
        bid_amount = DAILY_SALARY * 0.85
    elif my_hp <= 6: # Moderate HP: bid strongly
        bid_amount = DAILY_SALARY * 0.7
    else: # Healthy HP: can be more strategic
        bid_amount = DAILY_SALARY * 0.55

    # Adjust based on number of opponents
    if num_alive_opponents == 0:
        # No competition, bid minimally to save budget, but ensure water if needed.
        if my_hp <= 2:
            bid_amount = max(bid_amount, 10.0) # Ensure it's not too low if critical
        else:
            bid_amount = min(bid_amount, DAILY_SALARY * 0.05) # Very low bid if healthy and alone
            bid_amount = max(bid_amount, 1.0) # Minimum bid
    else:
        # Adjust bid based on supply scarcity
        # If supply is low (e.g., barely enough for WATER_REQ), increase bid.
        # If supply is high (e.g., enough for multiple players), decrease bid slightly.
        if current_supply < WATER_REQ + (num_alive_opponents * WATER_REQ / 2): # Supply is somewhat scarce
            bid_amount *= 1.1 # Increase bid pressure
        elif current_supply > WATER_REQ + (num_alive_opponents * WATER_REQ): # Supply is quite abundant
            bid_amount *= 0.9 # Decrease bid pressure

        # Incorporate opponent's previous bids (this block will not run on Day 1 of Meta-Round 1)
        yesterday_bids = []
        for opp in alive_opponents:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            if highest_prev_bid >= DAILY_SALARY * 0.85: # Opponents were very aggressive
                if my_hp > 3: # If healthy, try to save a bit but still competitive
                    bid_amount = max(bid_amount, highest_prev_bid * 0.9)
                else: # Not healthy, must win
                    bid_amount = max(bid_amount, highest_prev_bid * 1.05 + 1)
            else: # Opponents were moderate or low
                bid_amount = max(bid_amount, highest_prev_bid + 2)

    # Ensure bid is within budget and non-negative
    final_bid = min(my_budget, max(0.0, bid_amount))

    # Ensure bid is at least 1 if I have budget and need water
    if my_budget > 0 and final_bid < 1.0:
        final_bid = 1.0

    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # Hardcoded from meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no alive opponents, bid low to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # 1. Look at yesterday's situation (Trace) for alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Calculate total water demand and supply
    total_water_demand = WATER_REQ
    for opp in alive_opponents:
        total_water_demand += opp['water_requirement']
    
    supply = day_context['supply']
    
    # Check if water is scarce (more demand than supply)
    is_water_scarce = total_water_demand > supply

    # 2. Decision logic based on my status and opponent's previous bids
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    # If I'm in critical condition (low HP or multiple no-water days), bid aggressively
    if my_hp <= 3 or my_no_water_days >= 1:
        # If budget is very low, bid almost all of it to survive
        if my_budget < DAILY_SALARY * 0.8:
            return min(my_budget, DAILY_SALARY * 0.98) # Bid very high, almost all budget
        return min(my_budget, DAILY_SALARY * 0.9) # High bid to secure water

    # If there are previous bids from opponents
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If water is scarce, or I have moderate HP, react to highest previous bid
        if is_water_scarce or my_hp <= 5:
            # If highest opponent bid was very high, I need to match or slightly exceed
            if highest_prev_bid >= DAILY_SALARY * 0.75:
                # If I have decent budget, try to outbid
                if my_budget > highest_prev_bid + 10:
                    return min(my_budget, highest_prev_bid + 5)
                # Otherwise, bid a solid amount, but don't overspend if budget is tight
                return min(my_budget, DAILY_SALARY * 0.8) # Strong bid
            else: # Opponents not bidding extremely high, try to win efficiently
                return min(my_budget, max(DAILY_SALARY * 0.55, highest_prev_bid + 3)) # Slightly above them
        else: # Water is not scarce, and my HP is good, so can try to conserve
            return min(my_budget, DAILY_SALARY * 0.5) # Bid moderately
    
    # If no previous bids or first day, use a default strategy
    # This might happen on day 1 or if all previous high bidders died.
    if my_hp <= 5:
        return min(my_budget, DAILY_SALARY * 0.7) # Moderate-high bid
    return min(my_budget, DAILY_SALARY * 0.55) # Default moderate bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    my_current_bid = 0.0

    # Base bid strategy based on my HP
    if my_status['hp'] <= 2: # Critical health
        my_current_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5: # Low health
        my_current_bid = DAILY_SALARY * 0.75
    else: # Healthy
        my_current_bid = DAILY_SALARY * 0.55

    # Adjust based on yesterday's highest opponent bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If I need water critically, ensure I bid above yesterday's high
        if my_status['hp'] <= 2:
            my_current_bid = max(my_current_bid, highest_prev_bid + 5.0) 
        # If I need water, but not critically, bid competitively
        elif my_status['hp'] <= 5:
            my_current_bid = max(my_current_bid, highest_prev_bid + 1.0) 
        # If healthy, try to conserve but react if competition was fierce
        else:
            if highest_prev_bid >= DAILY_SALARY * 0.8: # If competition was fierce yesterday
                my_current_bid = max(my_current_bid, DAILY_SALARY * 0.6) 
            else:
                my_current_bid = min(my_current_bid, highest_prev_bid + 1.0) 

    # Ensure bid doesn't exceed budget and is non-negative
    final_bid = min(my_status['budget'], my_current_bid)
    
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQ = 13
    MY_DAILY_SALARY = 150
    EPISODE_DAYS = 10

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents remain, bid minimally to secure water
    if not alive_opponents:
        return min(my_budget, MY_DAILY_SALARY * 0.1)

    # Analyze yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid: a strong starting point, assuming competitive environment
    target_bid = MY_DAILY_SALARY * 0.8

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Adjust bid based on my HP and highest previous bid
        if my_hp <= 2: # Critical HP, must win at almost any cost
            target_bid = highest_prev_bid + (MY_DAILY_SALARY * 0.15) # Bid 15% of salary above
            target_bid = max(target_bid, MY_DAILY_SALARY * 1.1) # Ensure it's at least 110% of my salary
        elif my_hp <= 5: # Low-moderate HP, need to be very competitive
            target_bid = highest_prev_bid + (MY_DAILY_SALARY * 0.07) # Bid 7% of salary above
            target_bid = max(target_bid, MY_DAILY_SALARY * 0.95) # Ensure it's at least 95% of my salary
        else: # Healthy HP, can try to conserve budget but still aim to win
            target_bid = highest_prev_bid + (MY_DAILY_SALARY * 0.03) # Bid 3% of salary above
            target_bid = max(target_bid, MY_DAILY_SALARY * 0.8) # Ensure it's at least 80% of my salary
    
    # If it's the very last day or I'm critically low on HP and need water
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 1: # Last day or second to last day
        if my_no_water_days > 0 or my_hp < 10: # If I've lost HP or haven't fully survived
            return my_budget # Bid everything to survive
        else: # Last day, high HP, just need to secure the win
            target_bid = max(target_bid, MY_DAILY_SALARY * 0.9)

    # Ensure the bid does not exceed my current budget
    # Ensure a minimum bid to actually be considered competitive for water
    final_bid = min(my_budget, max(target_bid, MY_DAILY_SALARY * 0.1))

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
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    current_day = day_context['day']
    days_left = EPISODE_DAYS - current_day

    bid = DAILY_SALARY * 0.6

    if my_current_hp <= 3:
        bid = DAILY_SALARY * 1.2
    elif my_current_hp <= 6:
        bid = DAILY_SALARY * 0.9

    if my_status['no_water_days'] > 0:
        bid = max(bid, DAILY_SALARY * 1.0)

    if days_left <= 2:
        bid = max(bid, DAILY_SALARY * 1.5)
    elif days_left <= 4:
        bid = max(bid, DAILY_SALARY * 1.1)

    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            bid = max(bid, highest_prev_bid + 10)
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            bid = max(bid, highest_prev_bid + 5)
        else:
            bid = min(bid, highest_prev_bid + 20)

    if day_context['supply'] >= 22:
        bid *= 0.9
    elif day_context['supply'] <= 18:
        bid *= 1.1

    final_bid = max(1.0, min(my_current_budget, bid))

    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQUIREMENT = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        return max(1.0, min(my_current_budget, DAILY_SALARY * 0.1))

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    my_bid = 0.0
    if my_current_hp <= 2:
        my_bid = DAILY_SALARY * 0.95
    elif my_current_hp <= 4:
        my_bid = DAILY_SALARY * 0.8
    else:
        my_bid = DAILY_SALARY * 0.55

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        water_per_participant = current_supply / (num_alive_opponents + 1)

        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_current_hp > 3:
                if water_per_participant >= WATER_REQUIREMENT * 1.5:
                    my_bid = min(my_bid, highest_prev_bid * 0.9)
                else:
                    my_bid = max(my_bid, highest_prev_bid + 2.0)
            else:
                my_bid = max(my_bid, highest_prev_bid + 5.0)
        else:
            if water_per_participant < WATER_REQUIREMENT * 1.2:
                my_bid = max(my_bid, highest_prev_bid + 5.0)
            else:
                my_bid = max(my_bid, highest_prev_bid + 1.0)
                my_bid = min(my_bid, DAILY_SALARY * 0.6)

    my_bid = max(my_bid, DAILY_SALARY * 0.2)

    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_current_hp > 0:
        my_bid = max(my_bid, DAILY_SALARY * 0.85)
    elif remaining_days <= 4 and my_current_hp <= 2:
        my_bid = max(my_bid, DAILY_SALARY * 0.99)

    my_bid = min(my_current_budget, my_bid)
    
    my_bid = max(1.0, my_bid)

    return my_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    remaining_days = EPISODE_DAYS - current_day

    # Base bid: aim for profit, but be competitive. David bids high, others less so.
    base_bid = DAILY_SALARY * 0.65 # Initial competitive bid (97.5)

    # --- Adjust bid based on my HP and no_water_days (Urgency) ---
    if my_hp <= 2 or my_no_water_days >= 2: # Critical state: Must win water
        base_bid = DAILY_SALARY * 0.95 # Bid very aggressively (142.5)
    elif my_hp <= 4 or my_no_water_days >= 1: # Urgent state: High need for water
        base_bid = DAILY_SALARY * 0.85 # Bid strongly (127.5)
    elif my_hp <= 6: # Moderate urgency: Need to secure water soon
        base_bid = DAILY_SALARY * 0.75 # (112.5)

    # --- Adjust bid based on remaining days (End game pressure) ---
    if remaining_days <= 2: # Last 2 days: High pressure to survive
        base_bid *= 1.15 # Increase bid significantly
    elif remaining_days <= 4: # Mid-late game: Pressure increasing
        base_bid *= 1.08 # Increase bid
    elif remaining_days <= 6: # Mid game: Slight increase to stay competitive
        base_bid *= 1.03

    # --- Adjust bid based on opponent's previous bids (Competitive reaction) ---
    alive_opponents = [o for o_id, o in opponents_status.items() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest opponent bid was very high, it indicates strong competition
        if highest_prev_bid > DAILY_SALARY * 0.9: # Very aggressive opponent (e.g., > 135)
            if my_hp <= 4 or my_no_water_days >= 1: # I need water badly
                base_bid = max(base_bid, highest_prev_bid + 10) # Try to beat them significantly
            else: # I can afford to let them win if they overbid, or stay competitive
                base_bid = max(base_bid, highest_prev_bid * 0.98) # Stay very close
        elif highest_prev_bid > DAILY_SALARY * 0.7: # Moderately aggressive (e.g., > 105)
            if my_hp <= 4 or my_no_water_days >= 1:
                base_bid = max(base_bid, highest_prev_bid + 5) # Try to beat them
            else:
                base_bid = max(base_bid, highest_prev_bid * 0.95) # Stay competitive
        else: # Low previous bids, maybe I can save money
            # Ensure I still bid enough to win against low bidders, but don't overpay.
            # Bid slightly above their max low bid, but not below a certain threshold.
            base_bid = max(base_bid, min(highest_prev_bid + (DAILY_SALARY * 0.1), DAILY_SALARY * 0.7))

    # --- Final bid constraints ---
    # Never bid more than current budget
    final_bid = min(base_bid, my_budget)

    # Ensure a minimum bid if I have budget, especially if I need water.
    if my_budget > 0:
        if my_hp <= 2 or my_no_water_days >= 2: # Desperate, ensure a strong bid
            final_bid = max(final_bid, DAILY_SALARY * 0.7)
        else: # General minimum bid to stay in game, if not desperate
            final_bid = max(final_bid, DAILY_SALARY * 0.2)
    else: # If budget is 0, bid 0
        final_bid = 0.0

    # Ensure bid is always non-negative
    final_bid = max(0.0, final_bid)

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid conservatively to save budget unless HP is critical
    if not alive_opponents:
        if my_status['hp'] <= 3:
            return min(my_status['budget'], DAILY_SALARY * 0.6)
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_bid = 0.0

    # If no previous bids (e.g., Day 1 of the episode)
    if not yesterday_bids or day_context['day'] == 1:
        if my_status['hp'] <= 3: # Critical HP
            current_bid = DAILY_SALARY * 0.9
        elif my_status['hp'] <= 5: # Low HP
            current_bid = DAILY_SALARY * 0.7
        else: # Healthy HP
            current_bid = DAILY_SALARY * 0.5
    else:
        highest_prev_bid = max(yesterday_bids)

        # React to opponent's highest previous bid based on my HP and opponent aggression
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents are bidding high
            if my_status['hp'] <= 3: # Critical HP, must win
                current_bid = max(highest_prev_bid + 5, DAILY_SALARY * 0.95)
            elif my_status['hp'] <= 5: # Low HP, need water
                current_bid = max(highest_prev_bid + 2, DAILY_SALARY * 0.85)
            else: # Healthy HP, but competition is high, stay competitive
                current_bid = max(highest_prev_bid + 1, DAILY_SALARY * 0.7)
        else: # Opponents are bidding moderately or low
            if my_status['hp'] <= 3: # Critical HP, bid high to secure
                current_bid = max(highest_prev_bid + 5, DAILY_SALARY * 0.9)
            elif my_status['hp'] <= 5: # Low HP, bid slightly above highest to secure
                current_bid = max(highest_prev_bid + 1, DAILY_SALARY * 0.75)
            else: # Healthy HP, try to get it cheaper, but still competitive
                current_bid = max(highest_prev_bid * 1.05, DAILY_SALARY * 0.55)

    # Late game aggression (last 2 days)
    if day_context['day'] >= EPISODE_DAYS - 1:
        if my_status['hp'] <= 5: # If not super healthy, be very aggressive to survive final days
            current_bid = max(current_bid, DAILY_SALARY * 0.98)
        else: # If healthy, still be competitive but don't overspend if not necessary
            current_bid = max(current_bid, DAILY_SALARY * 0.8)

    # Ensure bid doesn't exceed budget
    final_bid = min(my_status['budget'], current_bid)

    # Ensure bid is at least a small amount if budget allows, to participate
    if final_bid <= 0 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], 0.01)
    elif final_bid < 0: # Should not happen with min(budget, current_bid) but as a safeguard
        final_bid = 0.0

    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQUIREMENT = 13
    MY_DAILY_SALARY = 150
    EPISODE_DAYS = 10 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], MY_DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = MY_DAILY_SALARY * 0.8

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        target_bid = highest_prev_bid + 5.0 
        target_bid = max(target_bid, base_bid)
    else:
        target_bid = base_bid

    if my_status['hp'] <= 2: 
        target_bid = max(target_bid, MY_DAILY_SALARY * 1.3) 
        if yesterday_bids:
            target_bid = max(target_bid, max(yesterday_bids) + 15.0)
    elif my_status['hp'] <= 4: 
        target_bid = max(target_bid, MY_DAILY_SALARY * 1.05) 
        if yesterday_bids:
            target_bid = max(target_bid, max(yesterday_bids) + 10.0)
    elif my_status['hp'] <= 6: 
        target_bid = max(target_bid, MY_DAILY_SALARY * 0.9) 

    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: 
        target_bid = max(target_bid, MY_DAILY_SALARY * 1.2) 
        if yesterday_bids:
            target_bid = max(target_bid, max(yesterday_bids) + 12.0)
    elif remaining_days <= 4: 
        target_bid = max(target_bid, MY_DAILY_SALARY * 1.0) 

    final_bid = min(my_status['budget'], target_bid)
    final_bid = max(0.0, final_bid)

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

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    bid_value = 0.0

    # Base bid strategy based on HP and recent water deprivation
    if my_hp <= 2 or my_no_water_days >= 1:
        bid_value = DAILY_SALARY * 1.2 # Very aggressive
    elif my_hp <= 4:
        bid_value = DAILY_SALARY * 0.9 # Aggressive
    else:
        bid_value = DAILY_SALARY * 0.7 # Moderate

    # Adjust based on opponent's previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid > DAILY_SALARY: # Opponent was extremely aggressive
            if my_hp <= 2 or my_no_water_days >= 1:
                bid_value = max(bid_value, highest_prev_bid + 5) # Try to beat it if desperate
            else:
                bid_value = max(bid_value, highest_prev_bid * 0.95) # Match closely, but don't overspend if not desperate
        elif highest_prev_bid >= DAILY_SALARY * 0.7: # Opponent was moderately aggressive
            bid_value = max(bid_value, highest_prev_bid + 2) # Slightly outbid
        else: # Opponent was conservative
            bid_value = max(bid_value, highest_prev_bid + 1) # Just a bit more to win
    
    # On the last day, if we have budget and need water, bid very high to secure the win.
    if current_day == EPISODE_DAYS and my_hp > 0:
        bid_value = max(bid_value, DAILY_SALARY * 1.5)

    # Ensure bid does not exceed current budget
    bid_value = min(my_budget, bid_value)

    # Ensure a minimal bid if we need water and budget allows
    if my_hp > 0 and bid_value < 1.0 and my_budget > 0:
        bid_value = 1.0
    
    # If budget is very low and we still need water, bid most of what's left
    if my_budget > 0 and my_hp <= 2 and bid_value < my_budget * 0.5:
        bid_value = my_budget * 0.9

    return float(bid_value)
"""
