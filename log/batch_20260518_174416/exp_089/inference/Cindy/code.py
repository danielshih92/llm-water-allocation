# ============================================================
# Experiment: exp_089
# Agent: Cindy
# Source: exp_089
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

    # Filter alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to get water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    # --- Initial Bid (Conservative) ---
    # Start with a bid that is generally profitable
    bid = DAILY_SALARY * 0.4 # Default conservative bid

    # --- HP Adjustment ---
    # Prioritize survival if HP is low
    if my_status['hp'] <= 2: # Critical HP
        bid = DAILY_SALARY * 0.95 # Very aggressive
    elif my_status['hp'] == 3: # Warning HP
        bid = max(bid, DAILY_SALARY * 0.7) # Aggressive
    # If HP is high (4 or 5), keep bid conservative or slightly higher if competition demands

    # --- Opponent Bid Adjustment (from previous_trace) ---
    yesterday_bids = []
    total_opponent_water_req = 0
    for opp in alive_opponents:
        total_opponent_water_req += opp['water_requirement']
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    # If opponents bid high yesterday, we might need to increase our bid
    # This is a reactive component
    if max_yesterday_bid > DAILY_SALARY * 0.6: # If max opponent bid was aggressive
        if my_status['hp'] <= 3: # If I also need water
            bid = max(bid, max_yesterday_bid + 5) # Bid slightly above
        else: # If my HP is good, try to outbid but don't overspend too much
            bid = max(bid, max_yesterday_bid + 1) # Small increment

    # --- Supply Scarcity Adjustment ---
    total_water_demand = WATER_REQ + total_opponent_water_req
    current_supply = day_context['supply']

    supply_demand_ratio = current_supply / total_water_demand if total_water_demand > 0 else 100.0

    # Adjust bid based on supply scarcity and number of opponents
    if supply_demand_ratio < 1.0: # Supply less than total demand
        bid = max(bid, DAILY_SALARY * 0.95) # Very aggressive
    elif supply_demand_ratio < 1.5: # Supply is tight
        bid = max(bid, DAILY_SALARY * 0.75) # Aggressive
    elif supply_demand_ratio > 2.0: # Supply is abundant
        # If HP is good, try to bid lower
        if my_status['hp'] >= 4:
            bid = min(bid, DAILY_SALARY * 0.3) # Very conservative
        else: # Even with abundant supply, if HP is low, maintain a moderate bid
            bid = min(bid, DAILY_SALARY * 0.5)
    elif num_alive_opponents == 1 and supply_demand_ratio > 1.5: # Only one opponent, supply is good
        # Try to bid just enough to win, or slightly above a low bid
        bid = min(bid, DAILY_SALARY * 0.45) # Moderate conservative bid

    # Ensure bid doesn't exceed budget or salary
    final_bid = min(my_status['budget'], bid)
    final_bid = min(final_bid, DAILY_SALARY) # Never bid more than daily salary to ensure profit potential

    # Ensure bid is at least 1 to be considered
    final_bid = max(1, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents are alive, bid just enough to secure water at a low cost
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Get yesterday's bids from previous_trace for immediate reaction
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_supply = day_context['supply']
    current_day = day_context['day']
    remaining_days = EPISODE_DAYS - current_day

    # Base bid strategy: Adjust based on supply scarcity
    # Supply range: 15-25. My WATER_REQ: 13. Supply is always competitive.
    base_bid = DAILY_SALARY * 0.55 # Default moderate bid

    if current_supply <= 17: # Very low supply, high competition
        base_bid = DAILY_SALARY * 0.75 
    elif current_supply <= 20: # Low supply
        base_bid = DAILY_SALARY * 0.65
    else: # Moderate supply (21-25)
        base_bid = DAILY_SALARY * 0.55

    # React to yesterday's highest bid to adapt to opponent aggression
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.85: # Opponents were very aggressive
            if my_status['hp'] > 4: # If HP is good, be competitive but save some budget
                base_bid = max(base_bid, DAILY_SALARY * 0.7)
            else: # Low HP, must compete hard
                base_bid = max(base_bid, highest_prev_bid + 5)
                base_bid = min(base_bid, DAILY_SALARY * 0.99) # Cap at near max salary
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # Moderate opponent aggression
            base_bid = max(base_bid, highest_prev_bid + 1) # Slightly outbid
        else: # Low opponent bids, try to save money
            base_bid = min(base_bid, highest_prev_bid + 5)
            base_bid = max(base_bid, DAILY_SALARY * 0.4) # Ensure a minimum bid to stay relevant

    # CRITICAL: Survival logic - if HP is low, bid very aggressively
    final_bid = base_bid

    if my_status['hp'] <= 2: # Very critical HP, near death
        final_bid = DAILY_SALARY * 0.99 # Bid almost everything to survive
    elif my_status['hp'] <= 4 and remaining_days <= 3: # Low HP and late in the game
        final_bid = max(final_bid, DAILY_SALARY * 0.9)
    elif my_status['hp'] <= 4: # Just low HP
        final_bid = max(final_bid, DAILY_SALARY * 0.8)
    
    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], final_bid)
    
    # Ensure bid is at least a minimal amount if water is needed for survival
    if my_status['hp'] < EPISODE_DAYS: # If I haven't secured water for all remaining days
        final_bid = max(final_bid, 1.0) # Bid at least 1 to participate

    # Final check to ensure bid is non-negative
    final_bid = max(0.0, final_bid)

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # 1. Base bid: A competitive starting point
    bid = DAILY_SALARY * 0.65

    # 2. Adjust bid based on my current HP (most critical factor for survival)
    if my_status['hp'] <= 2: # Critical HP
        bid = DAILY_SALARY * 0.99
    elif my_status['hp'] <= 5: # Low HP
        bid = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 7: # Medium HP
        bid = DAILY_SALARY * 0.8

    # 3. Adjust bid for end-game urgency
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: # Last 2 days
        if my_status['hp'] <= 5: # If still struggling, bid maximum to survive
            bid = DAILY_SALARY * 0.99
        else: # If healthy, secure water with a strong bid
            bid = max(bid, DAILY_SALARY * 0.85)

    # 4. Adjust bid based on opponent behavior (yesterday's trace)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents bid aggressively, I must match or slightly exceed
        if highest_prev_bid > DAILY_SALARY * 0.5:
            bid = max(bid, highest_prev_bid + 2.0)
        else: # Opponents bid low or negligibly
            # If healthy, I can afford to bid lower, but still ensure winning if others bid 0
            if my_status['hp'] > 5:
                bid = min(bid, DAILY_SALARY * 0.3)
            else: # If low HP, still need to secure water, even if opponents bid low
                bid = max(bid, DAILY_SALARY * 0.6)

    # 5. Adjust bid based on supply relative to competition
    # Given WATER_REQ = 13 and supply_range [15, 25], supply is almost always tight.
    # Usually enough for one full requirement, or one full + some leftover.
    # Competition for the primary 'slot' is high.
    if day_context['supply'] <= WATER_REQ + 2: # Very tight supply (15-17 units)
        bid = max(bid, DAILY_SALARY * 0.88) # Be very aggressive
    elif day_context['supply'] >= WATER_REQ * 2 - 2: # Relatively more supply (24-25 units)
        # Still not enough for two full, but less tight. Can be slightly less aggressive if healthy.
        if my_status['hp'] > 5:
            bid = min(bid, DAILY_SALARY * 0.70) # Cap it if healthy
        else: # Still need to be aggressive if HP is low
            bid = max(bid, DAILY_SALARY * 0.8)

    # 6. If no opponents are alive, bid minimally to save budget
    if num_alive_opponents == 0:
        bid = DAILY_SALARY * 0.1

    # 7. Final bid must be affordable and non-negative
    final_bid = min(my_status['budget'], bid)
    final_bid = max(0.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_HP_CRITICAL = 2 # If HP is 2 or less, bid very aggressively
    MIN_HP_LOW = 4      # If HP is 4 or less, bid aggressively

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to get water and save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    current_bid = 0.0

    if my_status['hp'] <= MIN_HP_CRITICAL:
        # Critical HP, bid very aggressively, aiming to outbid even Alex (max bid 150.5)
        current_bid = DAILY_SALARY * 1.01 # Base 151.5
        if highest_prev_bid > DAILY_SALARY: # If yesterday's highest was already > 150
            current_bid = max(current_bid, highest_prev_bid + 2)
        elif highest_prev_bid > 0: # If there were bids, ensure we're above them
            current_bid = max(current_bid, highest_prev_bid + 1)
        else: # No previous bids, just bid high
            current_bid = max(current_bid, DAILY_SALARY * 0.95) # 142.5
    elif my_status['hp'] <= MIN_HP_LOW:
        # Low HP, bid aggressively
        current_bid = DAILY_SALARY * 0.9 # Base 135
        if highest_prev_bid > DAILY_SALARY * 0.8: # If yesterday's highest was > 120
            current_bid = max(current_bid, highest_prev_bid + 1)
        elif highest_prev_bid > 0:
            current_bid = max(current_bid, highest_prev_bid + 0.5)
        else:
            current_bid = max(current_bid, DAILY_SALARY * 0.85) # 127.5
    else: # Healthy HP (my_status['hp'] > MIN_HP_LOW)
        num_water_slots = int(day_context['supply'] / WATER_REQ)
        total_bidders = 1 + num_alive_opponents

        if num_water_slots < total_bidders:
            # Scarce supply, competition is high.
            # If highest_prev_bid was very high, it might be better to conserve budget.
            if highest_prev_bid > DAILY_SALARY * 0.9: # If highest_prev_bid was > 135
                current_bid = DAILY_SALARY * 0.6 # Back off, bid 90
            else:
                current_bid = DAILY_SALARY * 0.75 # Moderate bid 112.5
                if highest_prev_bid > DAILY_SALARY * 0.6: # If yesterday was competitive
                    current_bid = max(current_bid, highest_prev_bid + 1)
        else:
            # Abundant supply, competition is lower. Bid conservatively.
            current_bid = DAILY_SALARY * 0.5 # Base 75
            if highest_prev_bid > DAILY_SALARY * 0.5: # If yesterday was higher than our base
                current_bid = max(current_bid, highest_prev_bid + 0.5)
            elif highest_prev_bid > 0: # If there were bids, but low, bid slightly above
                current_bid = max(current_bid, highest_prev_bid + 0.1) # Small increment
            else:
                current_bid = DAILY_SALARY * 0.4 # Even lower if no competition (60)

    # Ensure bid is at least a minimal amount to be considered (e.g., 1.0)
    final_bid = max(1.0, current_bid)

    # Cap bid at current budget
    final_bid = min(my_status['budget'], final_bid)

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimum to secure water
    if num_alive_opponents == 0:
        return min(my_status['budget'], 1.0)

    # Calculate initial bid based on my health and day
    bid_amount = DAILY_SALARY * 0.5 # Start with a moderate bid

    # Adjust bid if my HP is low (desperation)
    if my_status['hp'] <= WATER_REQ * 1.5: # Critical or near critical HP
        bid_amount = DAILY_SALARY * 0.7
    if my_status['hp'] <= WATER_REQ: # Very critical, must get water
        bid_amount = DAILY_SALARY * 0.95
    
    # If I missed water yesterday, increase bid
    if my_status['no_water_days'] > 0:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.8) # Ensure it's at least this high if I missed water

    # Adjust bid based on current supply
    supply_level = day_context['supply']
    normalized_supply = (supply_level - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    
    if normalized_supply < 0.3: # Low supply, increase bid
        bid_amount *= 1.15
    elif normalized_supply > 0.7: # High supply, decrease bid slightly
        bid_amount *= 0.9

    # React to opponents' previous bids (from previous_trace)
    yesterday_opp_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_opp_bids.append(prev_trace['bid'])

    if yesterday_opp_bids:
        max_yesterday_bid = max(yesterday_opp_bids)

        # If opponents bid very high yesterday, we need to be very competitive
        if max_yesterday_bid >= DAILY_SALARY * 0.8:
            bid_amount = max(bid_amount, max_yesterday_bid + (DAILY_SALARY * 0.1)) # Bid significantly higher than max
        # If opponents bid moderately high, bid slightly above their max
        elif max_yesterday_bid >= DAILY_SALARY * 0.5:
            bid_amount = max(bid_amount, max_yesterday_bid + 5.0) # Bid slightly above max
        # If bids were generally low, try to win cheaply but still ensure water
        else:
            bid_amount = max(bid_amount, max_yesterday_bid + 1.0) # Bid just a bit above max to secure win

    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], bid_amount)

    # Ensure bid is not negative
    return max(0.0, final_bid)
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
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and prev.get('bid') > 0 and prev.get('status') == 'active':
            yesterday_bids.append(prev['bid'])

    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.7)
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            return min(my_status['budget'], max(DAILY_SALARY * 0.65, highest_prev_bid + 2))
        
        else:
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1))
    
    return min(my_status['budget'], DAILY_SALARY * 0.75)
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

    # Base bid, adjusted for my HP
    if my_status['hp'] <= 2: # Critical HP
        my_bid = DAILY_SALARY * 0.95 # Bid very high
    elif my_status['hp'] <= 4: # Low HP
        my_bid = DAILY_SALARY * 0.8 # Bid high
    else:
        my_bid = DAILY_SALARY * 0.6 # Moderate bid

    # If no opponents, bid conservatively
    if not alive_opponents:
        my_bid = min(my_bid, DAILY_SALARY * 0.4)
        return max(0.0, min(my_status['budget'], my_bid))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest previous bid was high, try to outbid it
        if highest_prev_bid >= DAILY_SALARY * 0.7: # e.g., highest bid >= 105
            my_bid = max(my_bid, highest_prev_bid + 2.0)
        # If highest previous bid was low, don't overpay
        elif highest_prev_bid < DAILY_SALARY * 0.4: # e.g., highest bid < 60
            my_bid = min(my_bid, highest_prev_bid + 5.0)
            my_bid = max(my_bid, DAILY_SALARY * 0.45) # Ensure a floor
    else:
        # If no previous bids (e.g., Day 1 or all opponents died yesterday), my_bid is already set based on HP
        pass

    # Further adjustment for very tight supply
    # If supply is barely enough for one agent's requirement
    if day_context['supply'] <= WATER_REQ + 2: # e.g. supply <= 15.0
        my_bid = max(my_bid, DAILY_SALARY * 0.85) # Bid very aggressively

    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], my_bid)

    # Ensure a minimum bid if I desperately need water or to stay alive
    if my_status['no_water_days'] > 0 or my_status['hp'] <= 5:
        final_bid = max(final_bid, DAILY_SALARY * 0.4)

    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    # If supply is less than water requirement, no one gets water. Bid 0 to save budget.
    if day_context['supply'] < WATER_REQ:
        return 0.0

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid a very low amount to secure water cheaply
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Base bid, adjusted by urgency based on my health and no_water_days
    if my_status['hp'] <= 2: # Critical health
        base_bid = DAILY_SALARY * 0.95
    elif my_status['no_water_days'] >= 1: # Missed water yesterday, need it today
        base_bid = DAILY_SALARY * 0.85
    elif my_status['hp'] <= 5: # Low health, but not critical
        base_bid = DAILY_SALARY * 0.7
    else: # Healthy
        base_bid = DAILY_SALARY * 0.5

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Adjust bid based on opponents' previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest previous bid is very high, try to outbid it, especially if I need water.
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents are bidding aggressively
            if my_status['hp'] <= 5 or my_status['no_water_days'] >= 1: # I need water
                base_bid = max(base_bid, highest_prev_bid + 5.0) # Bid higher to ensure win
            else: # Healthy, might be able to let them overbid, or just match closely
                base_bid = max(base_bid, highest_prev_bid + 1.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.4: # Moderate opponent bids
            base_bid = max(base_bid, highest_prev_bid + 1.0)
        # If bids are low, my base_bid is probably already higher, so no change needed here.

    # Final bid must not exceed budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure bid is non-negative
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimal amount to get water
    if num_alive_opponents == 0:
        return min(my_budget, 1.0) if my_budget > 0 else 0.0

    # If budget is 0, cannot bid
    if my_budget == 0:
        return 0.0

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid calculation
    bid_amount = 0.0

    # Critical HP: Bid full salary to survive
    if my_hp <= 2:
        bid_amount = DAILY_SALARY * 1.0
    # Low HP or missed water yesterday: Bid aggressively
    elif my_hp <= 4 or my_no_water_days > 0:
        bid_amount = DAILY_SALARY * 0.9
    # Healthy: React to opponents and general strategy
    else:
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents very aggressive
            bid_amount = max(DAILY_SALARY * 0.85, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Opponents moderately aggressive
            bid_amount = max(DAILY_SALARY * 0.7, highest_prev_bid + 2)
        else: # Opponents less aggressive or no strong signal
            bid_amount = max(DAILY_SALARY * 0.6, highest_prev_bid + 1)

        # Ensure a minimum bid even if healthy and opponents were very passive
        bid_amount = max(bid_amount, DAILY_SALARY * 0.5)

    # End game adjustment: Increase aggression as days run out
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.95)
    elif remaining_days <= 4:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.85)

    # Always cap bid at current budget
    final_bid = min(my_budget, bid_amount)

    # Ensure bid is at least 1.0 if water is needed and budget allows
    if my_hp < 10 and my_budget > 0:
        final_bid = max(final_bid, 1.0)
    elif my_hp == 10 and num_alive_opponents > 0: # If full HP but opponents exist, still bid something reasonable to stay competitive
        final_bid = max(final_bid, DAILY_SALARY * 0.1) # A small bid to show presence
    
    # Final safeguard to ensure a minimal bid if there's competition and budget
    if final_bid < 1.0 and my_budget > 0 and num_alive_opponents > 0:
        final_bid = max(final_bid, 1.0)

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

    # If no opponents, bid conservatively but ensure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    remaining_days = EPISODE_DAYS - day_context['day']

    # --- Aggressive Bidding for Survival ---
    # If HP is very low, bid very aggressively
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 1.05)

    # If we missed water yesterday, we are falling behind, bid higher
    if my_status['no_water_days'] > 0:
        return min(my_status['budget'], DAILY_SALARY * 0.9)

    # --- Analyze Opponent's Previous Bids ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # --- Dynamic Bidding Strategy ---
    base_bid = DAILY_SALARY * 0.6 # A moderate starting point

    # Adjust bid based on highest previous bid
    if highest_prev_bid > 0:
        # If opponents are bidding high, we need to be competitive
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, highest_prev_bid * 1.05) # Try to outbid slightly
        else:
            base_bid = max(base_bid, highest_prev_bid + 5) # Slightly outbid previous high

    # Adjust bid based on supply
    # Supply is always tight (15-25 for 4 players needing 13 each = 52 total demand)
    # Competition will always be high.
    expected_players_needing_water = len(alive_opponents) + 1 # Including myself
    if day_context['supply'] < WATER_REQ * expected_players_needing_water * 0.5: # Very low supply relative to potential demand
        base_bid *= 1.2 # Increase bid significantly

    # Adjust bid based on remaining days
    # As days run out, survival becomes more critical
    if remaining_days <= 3: # Last few days
        base_bid = max(base_bid, DAILY_SALARY * 0.8) # Ensure high bid
        if my_status['hp'] > 5: # If HP is good, can be slightly less aggressive
            base_bid = max(base_bid, DAILY_SALARY * 0.7)
        else: # If HP is not great, be very aggressive
            base_bid = max(base_bid, DAILY_SALARY * 0.95)

    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], base_bid)

    return final_bid
"""
