# ============================================================
# Experiment: exp_108
# Agent: Cindy
# Source: exp_108
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    alive_opponents_count = len(alive_opponents)

    # Rule 1: Survival mode if HP is critical
    if my_status['hp'] <= 2:
        # Bid very high to ensure water, up to budget
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # Rule 2: No opponents left, bid minimally to get water
    if alive_opponents_count == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Rule 3: Strategic bidding based on supply and number of opponents (HP > 2)
    # Calculate how many "slots" of water (my_water_requirement units) are available
    available_water_slots = current_supply / WATER_REQ
    needed_slots = alive_opponents_count + 1 # Myself + all alive opponents

    bid_amount = DAILY_SALARY * 0.5 # Default moderate bid

    if available_water_slots < needed_slots:
        # Supply is tight. Competition is high. Bid more aggressively.
        # The more the shortfall, the higher the bid.
        shortfall_ratio = (needed_slots - available_water_slots) / needed_slots
        # Scale bid from 60% to 90% of daily salary based on shortfall
        bid_amount = DAILY_SALARY * (0.6 + shortfall_ratio * 0.3)
        # Ensure a strong minimum bid if supply is tight
        bid_amount = max(bid_amount, DAILY_SALARY * 0.7)
    else:
        # Supply is sufficient for everyone (at least one slot per person).
        # We can afford to be less aggressive.
        bid_amount = DAILY_SALARY * 0.4 # Moderate bid

    # Ensure bid does not exceed available budget
    return min(my_status['budget'], bid_amount)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.75 # Default competitive bid (112.5)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        base_bid = max(base_bid, highest_prev_bid + 2.0)
    
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4:
        return min(my_status['budget'], max(base_bid, DAILY_SALARY * 0.85))
    else:
        return min(my_status['budget'], base_bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid a minimal amount to get water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid based on my current HP
    if my_status['hp'] <= 2:
        # Critical HP, bid very aggressively
        bid = DAILY_SALARY * 1.6 
    elif my_status['hp'] <= 4:
        # Low HP, bid aggressively
        bid = DAILY_SALARY * 1.2
    else:
        # Healthy HP, bid moderately but still aiming to win
        bid = DAILY_SALARY * 0.9

    # Further adjust bid based on opponent's previous behavior
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if my_status['hp'] <= 2:
            # Critical, try to beat highest_prev_bid + a small margin
            bid = max(bid, highest_prev_bid + 5.0)
        elif my_status['hp'] <= 4:
            # Low HP, try to beat highest_prev_bid if it's not too high
            bid = max(bid, highest_prev_bid + 2.0)
        else:
            # Healthy, be competitive. Adjust based on supply.
            if day_context['supply'] <= 18.0: # Only enough for one person's full requirement
                bid = max(bid, highest_prev_bid + 1.0)
            else: # More supply, potentially less fierce competition
                bid = max(bid, highest_prev_bid * 0.95) # Try to get it cheaper if possible
                bid = max(bid, DAILY_SALARY * 0.7) # Ensure a minimum reasonable bid

    # Ensure bid does not exceed available budget and is at least 1.0
    final_bid = max(1.0, min(my_status['budget'], bid))

    return final_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to secure water
    if not alive_opponents:
        if my_status['hp'] > 3:
            return min(my_status['budget'], DAILY_SALARY * 0.3)
        return min(my_status['budget'], DAILY_SALARY * 0.6)

    # Get highest previous bid from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Calculate available water slots
    num_water_slots = int(day_context['supply'] // WATER_REQ)
    
    # Determine how many agents are actively competing for water
    num_competitors = len(alive_opponents) + 1 # +1 for myself

    # Base bid strategy
    base_bid = DAILY_SALARY * 0.35 # A moderate initial bid

    # Adjust bid based on HP
    if my_status['hp'] <= 2: # Very low HP, desperate
        base_bid = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.7
    elif my_status['hp'] <= 6: # Moderate HP
        base_bid = DAILY_SALARY * 0.55
    
    # Adjust bid based on previous opponent behavior
    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.7: # Opponent was very aggressive
            if my_status['hp'] > 3:
                base_bid = max(base_bid, highest_prev_bid + 5)
            else:
                base_bid = max(base_bid, highest_prev_bid + 10)
        elif highest_prev_bid >= DAILY_SALARY * 0.4: # Opponent was moderately aggressive
            base_bid = max(base_bid, highest_prev_bid + 2.5)
        else: # Opponent was low, but we still need to win
            base_bid = max(base_bid, highest_prev_bid + 1)

    # Consider supply. If only one slot and multiple competitors, bid higher.
    if num_water_slots == 1 and num_competitors > 1:
        if my_status['hp'] <= 4: # Desperate
            base_bid = max(base_bid, DAILY_SALARY * 0.8)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.6)
    
    # Ensure bid doesn't exceed budget
    final_bid = min(my_status['budget'], base_bid)
    
    # Ensure bid is at least a minimal amount to be considered active
    final_bid = max(final_bid, 1.0) # Avoid bidding 0 unless budget is 0

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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        if my_hp < 5 or my_status['no_water_days'] > 0:
            return min(my_budget, DAILY_SALARY * 0.05)
        return 0.0

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    bid = DAILY_SALARY * 0.55

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_hp <= 3:
                bid = DAILY_SALARY * 0.95
            elif my_hp <= 6:
                bid = max(highest_prev_bid + 1.5, DAILY_SALARY * 0.8)
            else:
                bid = max(highest_prev_bid + 0.5, DAILY_SALARY * 0.6)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            if my_hp <= 4:
                bid = DAILY_SALARY * 0.85
            else:
                bid = max(highest_prev_bid + 1.0, DAILY_SALARY * 0.55)
        else:
            if my_hp <= 5:
                bid = DAILY_SALARY * 0.7
            else:
                bid = max(highest_prev_bid + 0.5, DAILY_SALARY * 0.4)
    else:
        if my_hp <= 3:
            bid = DAILY_SALARY * 0.85
        elif my_hp <= 6:
            bid = DAILY_SALARY * 0.65
        else:
            bid = DAILY_SALARY * 0.45

    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2:
        if my_hp <= 3:
            bid = DAILY_SALARY * 0.99
        elif my_hp > 7:
            bid = min(bid, DAILY_SALARY * 0.7)
    elif remaining_days <= 4:
        if my_hp <= 4:
            bid = bid * 1.1
        elif my_hp > 8:
            bid = bid * 0.9

    bid = min(bid, my_budget)

    if bid <= 0 and (my_status['no_water_days'] > 0 or my_hp < 5):
        bid = min(my_budget, DAILY_SALARY * 0.05)

    return max(0.0, bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
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
    num_alive_opponents = len(alive_opponents)

    available_water_slots = int(current_supply // WATER_REQ)

    base_bid = DAILY_SALARY * 0.5 # Default moderate bid

    # 1. Critical HP: Bid aggressively to survive
    if my_hp <= 2:
        return min(my_budget, DAILY_SALARY * 0.95)

    # 2. No water for a day: Need to secure water immediately
    if my_no_water_days > 0:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    # 3. Analyze yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None and prev_trace.get('status') != 'error':
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents bid very high yesterday and there's competition
        if max_yesterday_bid >= DAILY_SALARY * 0.8 and available_water_slots <= num_alive_opponents:
            if my_hp < 5: # My HP is not great, need to be competitive
                base_bid = max(base_bid, max_yesterday_bid * 1.05)
            else: # My HP is good, can try to conserve or slightly undercut
                base_bid = max(base_bid, max_yesterday_bid * 0.9)
        # If opponents bid moderately yesterday
        elif max_yesterday_bid > DAILY_SALARY * 0.4:
            base_bid = max(base_bid, avg_yesterday_bid * 1.05)
        # If opponents bid low yesterday
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.3)

    # 4. Adjust bid based on remaining days (end game)
    remaining_days = EPISODE_DAYS - current_day + 1
    if remaining_days <= 3:
        if my_hp < 5:
            base_bid = max(base_bid, DAILY_SALARY * 0.9)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.6)

    # 5. Abundant supply or no competition: Bid low (unless HP is critical)
    if available_water_slots > num_alive_opponents and my_hp > 2:
        base_bid = DAILY_SALARY * 0.25

    # Ensure bid is not negative and within budget
    final_bid = min(my_budget, max(0.0, base_bid))

    # If budget is very low and I need to survive, bid what I have
    if my_budget > 0 and my_hp <= 2:
        final_bid = my_budget
    elif my_budget < DAILY_SALARY * 0.5 and my_hp > 3: # Low budget, not critical HP
        final_bid = min(final_bid, DAILY_SALARY * 0.4) # Try to save

    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        # If no alive opponents, bid minimally to save budget.
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If the highest bid yesterday was very aggressive
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If my HP is good, try to conserve budget
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            # If my HP is low, bid aggressively to survive
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        
        # If the highest bid yesterday was not extremely aggressive, bid slightly above it
        return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))

    # If no yesterday's bids (e.g., first day or all opponents are new/no trace)
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    
    return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid: a percentage of daily salary
    # Start with a moderate bid, assuming I want water but don't want to overpay
    bid = DAILY_SALARY * 0.65

    # 1. Survival logic: If HP is critical, bid very high
    if my_hp <= 2:
        bid = DAILY_SALARY * 0.95 # Bid almost full salary to ensure survival
    elif my_hp <= 4:
        bid = DAILY_SALARY * 0.8 # High bid
    elif my_hp <= 6 and current_day > EPISODE_DAYS / 2: # Mid-game, moderate HP, need to secure water
        bid = DAILY_SALARY * 0.75

    # 2. React to opponent's yesterday's bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were very aggressive yesterday, I might need to raise my bid
        if highest_prev_bid >= DAILY_SALARY * 0.8: # High competition
            if my_hp <= 5: # If I need water, match or slightly exceed
                bid = max(bid, highest_prev_bid + (DAILY_SALARY * 0.05)) # Try to outbid by a small margin
            else: # If healthy, don't overpay too much unless supply is very low
                bid = max(bid, highest_prev_bid * 0.95) # Try to get it cheaper if possible, but stay competitive
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # Moderate competition
            if my_hp <= 3:
                bid = max(bid, highest_prev_bid + (DAILY_SALARY * 0.02))
            elif my_hp <= 7:
                bid = max(bid, highest_prev_bid * 1.01) # Slightly higher than highest
            else:
                bid = max(bid, highest_prev_bid * 0.98) # Try slightly lower

    # 3. Adjust for supply scarcity (relative to total demand)
    total_water_demand = WATER_REQ
    for opp in alive_opponents:
        total_water_demand += opp['water_requirement']

    if current_supply < total_water_demand: # Demand exceeds supply
        # Increase bid due to scarcity
        if my_hp <= 5:
            bid *= 1.1 # More aggressive increase if HP is low
        else:
            bid *= 1.05 # Moderate increase
    elif current_supply >= total_water_demand * 1.5: # Abundant supply
        # Decrease bid if supply is much higher than demand and I'm healthy
        if my_hp > 5:
            bid *= 0.95

    # 4. End-game pressure: Bid more aggressively as the game nears its end
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 3: # Last 3 days
        if my_hp < 10: # If not full health, prioritize survival
            bid = max(bid, DAILY_SALARY * 0.9)
        else: # Full health, but still need to secure water
            bid = max(bid, DAILY_SALARY * 0.75)


    # Final check: Ensure bid doesn't exceed budget and is at least a minimal value
    final_bid = min(my_budget, bid)
    final_bid = max(1.0, final_bid) # Minimum bid of 1.0

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        return int(min(my_status['budget'], DAILY_SALARY * 0.1))

    # --- Emergency / Desperation Bids ---
    if my_status['hp'] <= 2: # Critically low HP
        return int(min(my_status['budget'], DAILY_SALARY * 0.98))

    if day_context['day'] >= EPISODE_DAYS - 1: # Last two days
         return int(min(my_status['budget'], DAILY_SALARY * 0.9))

    # --- Analyze Opponent's Previous Bids ---
    strong_opponent_ids = ["Bob", "Eric"]
    strong_prev_bids = []
    all_prev_bids = []

    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                all_prev_bids.append(prev['bid'])
                if opp_id in strong_opponent_ids:
                    strong_prev_bids.append(prev['bid'])

    max_strong_prev_bid = 0
    if strong_prev_bids:
        max_strong_prev_bid = max(strong_prev_bids)

    max_all_prev_bid = 0
    if all_prev_bids:
        max_all_prev_bid = max(all_prev_bids)


    # --- Base Bid Calculation ---
    base_bid = DAILY_SALARY * 0.65 # A reasonable starting point

    # Prioritize strong opponents' high bids
    if max_strong_prev_bid > DAILY_SALARY * 0.85: # If strong opponents bid very high
        base_bid = max(base_bid, max_strong_prev_bid + 5)
    elif max_strong_prev_bid > DAILY_SALARY * 0.7: # If strong opponents bid moderately high
        base_bid = max(base_bid, max_strong_prev_bid + 2)
    elif max_all_prev_bid > DAILY_SALARY * 0.7: # If any opponent bid high
        base_bid = max(base_bid, max_all_prev_bid + 1)


    # Adjust bid based on supply scarcity
    if day_context['supply'] <= MIN_SUPPLY + 2: # Very low supply (15-17)
        base_bid *= 1.15
    elif day_context['supply'] <= (MIN_SUPPLY + MAX_SUPPLY) / 2: # Medium-low supply (18-20)
        base_bid *= 1.05

    # Adjust bid based on my HP (less critical than emergency, but still important)
    if my_status['hp'] <= 4: # If HP is getting low but not critical
        base_bid = max(base_bid, DAILY_SALARY * 0.75)

    # Final bid adjustments
    final_bid = min(my_status['budget'], base_bid)
    final_bid = min(final_bid, DAILY_SALARY * 0.99) # Cap general bids to prevent overspending unnecessarily

    # Ensure bid is at least a reasonable minimum, especially if no strong bids yesterday
    final_bid = max(final_bid, DAILY_SALARY * 0.25) # Don't bid too low

    return int(final_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
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

    # Base bid strategy based on my HP and need
    if my_hp <= 2: # Critical HP
        bid = MY_DAILY_SALARY * 0.95 # 142.5
    elif my_no_water_days > 0: # Missed water yesterday
        bid = MY_DAILY_SALARY * 0.85 # 127.5
    elif my_hp <= 4: # Low HP
        bid = MY_DAILY_SALARY * 0.7 # 105
    else: # Healthy HP
        bid = MY_DAILY_SALARY * 0.55 # 82.5

    # Adjust based on opponent's previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest previous bid was very high (Alex's aggressive range)
        if highest_prev_bid >= MY_DAILY_SALARY * 0.8: # 120
            if my_hp > 4 and current_supply > MY_WATER_REQ * 1.5: # Healthy and supply not too tight
                bid = min(bid, MY_DAILY_SALARY * 0.3) # Let them overpay, conserve budget
            else: # Low HP or tight supply, must compete
                bid = max(bid, highest_prev_bid + 5.0) # Try to outbid
                bid = min(bid, MY_DAILY_SALARY * 0.98) # Cap to avoid bidding too much over salary
        # If highest previous bid was moderate
        elif highest_prev_bid >= MY_DAILY_SALARY * 0.5: # 75
            bid = max(bid, highest_prev_bid + 2.0) # Slightly outbid to secure
            if current_supply >= MY_WATER_REQ * (num_alive_opponents + 1): # Abundant supply
                bid = min(bid, MY_DAILY_SALARY * 0.6) # Don't overpay
        # If highest previous bid was low (Bob's conservative range)
        else: # highest_prev_bid < 75
            bid = min(bid, MY_DAILY_SALARY * 0.5) # 75, secure water without overpaying

    # Final adjustment based on supply scarcity if not covered by previous logic
    # This ensures that even if opponents bid low, but supply is scarce, I still bid enough
    if current_supply < MY_WATER_REQ * (num_alive_opponents + 0.5): # Very tight supply for multiple agents
        if my_hp <= 6: # Need water more
            bid = max(bid, MY_DAILY_SALARY * 0.8) # Increase bid
        else: # Can afford to be slightly less aggressive if healthy
            bid = max(bid, MY_DAILY_SALARY * 0.65)

    # End game push
    if current_day >= EPISODE_DAYS - 2: # Last two days
        if my_hp <= 6: # Need to survive
            bid = max(bid, MY_DAILY_SALARY * 0.9)
        else: # If healthy, can try to win more aggressively
            bid = max(bid, MY_DAILY_SALARY * 0.7)

    # Ensure bid doesn't exceed budget
    final_bid = min(my_budget, bid)

    # Ensure bid is positive and reasonable (not ridiculously small)
    return max(0.0, final_bid)
"""
