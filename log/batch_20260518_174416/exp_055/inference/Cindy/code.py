# ============================================================
# Experiment: exp_055
# Agent: Cindy
# Source: exp_055
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150 # My daily salary

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents are alive, bid minimum to get water
    if not alive_opponents:
        return min(my_status['budget'], 1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # --- Core Bidding Logic ---
    # Case 1: React to yesterday's highest bid if available
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were very aggressive yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # I'm healthy, can afford to conserve budget or let them overspend
                # Bid lower, but still enough to potentially win if supply is high
                return min(my_status['budget'], DAILY_SALARY * 0.4)
            else: # My HP is low (<=3), I need water, must compete aggressively
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        # If opponents were moderately aggressive or less
        else:
            # Aim to win by bidding slightly above the highest previous bid, but ensure it's at least a moderate bid
            # This covers cases where previous bids were low or moderate.
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 2))

    # Case 2: No yesterday's bids available (e.g., Day 1, or all opponents were inactive)
    # Default strategy based on my HP and general conditions
    if my_status['hp'] <= 2: # Critical HP, bid very high
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    elif my_status['hp'] == 3: # Low HP, bid high
        return min(my_status['budget'], DAILY_SALARY * 0.75)
    else: # Healthy HP (>3)
        # Consider supply and number of competitors
        # Estimate total water needed for all alive players + myself
        # Assuming all opponents also need WATER_REQ
        estimated_total_demand = WATER_REQ * (num_alive_opponents + 1)
        
        if day_context['supply'] >= estimated_total_demand:
            # Plenty of water for everyone, bid conservatively
            return min(my_status['budget'], DAILY_SALARY * 0.4)
        elif day_context['supply'] < WATER_REQ:
            # Supply is less than my own requirement, it's a desperate fight
            return min(my_status['budget'], DAILY_SALARY * 0.85)
        else:
            # Moderate competition, bid moderately
            return min(my_status['budget'], DAILY_SALARY * 0.6)
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

    current_day = day_context['day']
    remaining_days = EPISODE_DAYS - current_day

    # Critical HP and End-Game Logic
    if my_status['hp'] <= 2 or remaining_days <= 1:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # Base Bid based on Opponent Behavior
    base_bid = DAILY_SALARY * 0.55 # Default moderate bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents very aggressive
            if my_status['hp'] > 5: # Healthy, smart competitive
                if day_context['supply'] >= 22: # High supply, try to undercut
                    base_bid = max(DAILY_SALARY * 0.6, highest_prev_bid * 0.9)
                else: # Low supply, be aggressive
                    base_bid = max(DAILY_SALARY * 0.7, highest_prev_bid + 1.5)
            else: # Low/moderate HP (3-5), very aggressive
                base_bid = max(DAILY_SALARY * 0.85, highest_prev_bid + 2)
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Opponents moderately aggressive
            if my_status['hp'] > 7: # Very healthy, save
                base_bid = max(DAILY_SALARY * 0.35, average_prev_bid * 0.9)
            else: # Moderate HP (3-7), competitive
                base_bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 1)
        else: # Opponents conservative
            if my_status['hp'] > 5: # Healthy, save budget
                base_bid = DAILY_SALARY * 0.25
            else: # Moderate HP, ensure water but don't overspend
                base_bid = max(DAILY_SALARY * 0.4, highest_prev_bid + 0.5)
    else: # No previous bids (e.g., Day 1 or all previous bidders died)
        if my_status['hp'] <= 5: # Low HP
            base_bid = DAILY_SALARY * 0.7
        elif my_status['hp'] <= 7: # Moderate HP
            base_bid = DAILY_SALARY * 0.5
        else: # Healthy HP
            base_bid = DAILY_SALARY * 0.35

    my_bid = base_bid

    # Further adjustments based on my HP (escalate if not covered by critical logic)
    if my_status['hp'] <= 5:
        my_bid = max(my_bid, DAILY_SALARY * 0.7)
    elif my_status['hp'] <= 7:
        my_bid = max(my_bid, DAILY_SALARY * 0.5)

    # Further adjustments based on remaining days (escalate if not covered by critical logic)
    if remaining_days <= 3:
        my_bid = max(my_bid, DAILY_SALARY * 0.7)
    elif remaining_days <= 5:
        my_bid = max(my_bid, DAILY_SALARY * 0.6)

    # Adjust based on supply (lower supply means more competition)
    if day_context['supply'] <= 18:
        my_bid = max(my_bid, base_bid * 1.1)
    elif day_context['supply'] >= 22:
        my_bid = min(my_bid, base_bid * 0.9)

    my_bid = min(my_status['budget'], my_bid)
    my_bid = max(0.1, my_bid)

    return my_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQ = 13
    MY_DAILY_SALARY = 150
    EPISODE_DAYS = 10 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], MY_DAILY_SALARY * 0.1)

    yesterday_bids = []
    total_opponent_water_req = 0
    for opp in alive_opponents:
        total_opponent_water_req += opp['water_requirement']
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    total_demand = MY_WATER_REQ + total_opponent_water_req
    
    base_bid = MY_DAILY_SALARY * 0.55 

    if my_status['hp'] <= 2: 
        base_bid = MY_DAILY_SALARY * 0.95 
    elif my_status['hp'] <= 4: 
        base_bid = MY_DAILY_SALARY * 0.85 
    
    if my_status['no_water_days'] > 0:
        base_bid = max(base_bid, MY_DAILY_SALARY * 0.9) 

    if day_context['day'] >= EPISODE_DAYS - 2: 
        base_bid = max(base_bid, MY_DAILY_SALARY * 0.9) 
    elif day_context['day'] >= EPISODE_DAYS - 4: 
        base_bid = max(base_bid, MY_DAILY_SALARY * 0.75)
        
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= MY_DAILY_SALARY * 0.8: 
            if my_status['hp'] <= 3: 
                base_bid = max(base_bid, highest_prev_bid + 5) 
            else: 
                base_bid = max(base_bid, highest_prev_bid * 0.95) 
        elif highest_prev_bid >= MY_DAILY_SALARY * 0.5: 
            base_bid = max(base_bid, highest_prev_bid + 1) 
        else: 
            if my_status['hp'] > 5:
                base_bid = min(base_bid, MY_DAILY_SALARY * 0.4) 
            else:
                base_bid = max(base_bid, MY_DAILY_SALARY * 0.6) 
    
    if total_demand > 0: 
        supply_demand_ratio = day_context['supply'] / total_demand
        
        if supply_demand_ratio >= 1.5: 
            if my_status['hp'] > 5: 
                base_bid *= 0.8
            else: 
                base_bid *= 0.9
        elif supply_demand_ratio < 1.0: 
            base_bid *= 1.15 
            if my_status['hp'] <= 4:
                base_bid *= 1.1 
        elif supply_demand_ratio < 1.2: 
            base_bid *= 1.05 

    final_bid = min(my_status['budget'], base_bid)
    final_bid = max(final_bid, 1.0) 
    
    return round(final_bid, 2)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    DAYS_IN_EPISODE = 10 # From meta_round_state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid a minimal amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    # Calculate days left in the episode
    days_left = DAYS_IN_EPISODE - day_context['day']

    # --- Phase 1: Critical HP Bidding ---
    # If HP is very low (1 or 2), bid aggressively to survive.
    if my_status['hp'] <= 2:
        # Bid high, potentially more than daily salary if necessary for survival
        # This ensures survival is prioritized over budget accumulation.
        return min(my_status['budget'], DAILY_SALARY * 1.2) # Bid 180

    # --- Phase 2: Strategic Bidding based on Opponent Behavior and Game State ---
    
    # Collect yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid
    base_bid = DAILY_SALARY * 0.8 # Default bid (120) for normal days if no clear opponent signals

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If the highest bid yesterday was very high, we might want to slightly outbid it
        # or be more cautious if our HP is good to avoid a bidding war.
        if highest_prev_bid >= DAILY_SALARY * 1.0: # If yesterday's max bid was >= 150
            if my_status['hp'] > 3: # If not critical, try to conserve budget
                base_bid = max(highest_prev_bid * 0.98, DAILY_SALARY * 0.85) # Slightly less than highest, but still strong
            else: # If HP is somewhat low (3), still need to be very competitive
                base_bid = highest_prev_bid + 5.0 # Outbid by a small margin
        elif highest_prev_bid >= DAILY_SALARY * 0.8: # If yesterday's max bid was >= 120
            base_bid = highest_prev_bid + 3.0 # Slightly outbid
        else: # Yesterday's highest bid was low/moderate
            base_bid = highest_prev_bid + 5.0 # Outbid by a small margin to secure water
    
    # Adjust bid based on day progression (end game pressure)
    if days_left <= 2: # Last 2 days (Day 9, 10)
        base_bid *= 1.15 # Increase bid aggressiveness by 15%
    elif days_left <= 5: # Last 5 days (Day 6, 7, 8)
        base_bid *= 1.08 # Increase bid aggressiveness by 8%

    # Ensure the bid is at least a minimum reasonable amount to contend for water,
    # given the high competition (only 1 full water_req can be supplied).
    # A minimum of DAILY_SALARY * 0.6 (90) seems appropriate to stay in the game.
    final_bid = max(base_bid, DAILY_SALARY * 0.6)

    # Ensure the final bid does not exceed the agent's current budget
    return min(my_status['budget'], final_bid)
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
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)
    num_competitors = num_alive_opponents + 1 # Myself + opponents

    # If no opponents, bid conservatively
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Calculate available water slots
    num_water_slots = int(current_supply // WATER_REQ)

    # Determine if supply is tight (fewer slots than competitors)
    is_supply_tight = num_water_slots < num_competitors

    # --- Strategy based on my state and opponent's previous bids ---

    # 1. Desperation mode: If HP is very low or no water for a day
    # This is the highest priority - ensure survival at almost any cost
    if my_hp <= 2 or my_no_water_days >= 1:
        # Bid very aggressively to ensure survival, potentially spending most of budget.
        # Add a small buffer based on remaining days to slightly outbid if possible.
        desperation_bid = DAILY_SALARY * 1.2 + (EPISODE_DAYS - current_day) * 5
        return min(my_budget, desperation_bid)

    # 2. Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = 0
    avg_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)
    else:
        # If no previous bids (e.g., Day 1), estimate based on a competitive baseline.
        # Given general meta-round bids, a competitive range is 60-100.
        max_yesterday_bid = DAILY_SALARY * 0.7 # Assume some competition
        avg_yesterday_bid = DAILY_SALARY * 0.6

    # 3. Base bid calculation
    base_bid = DAILY_SALARY * 0.5 # A default competitive bid

    # Adjust based on supply tightness and competition
    if is_supply_tight:
        # If supply is tight, competition is fierce. Need to bid higher.
        if num_water_slots == 1 and num_competitors > 1: # Only one winner possible, high stakes
            base_bid = max(base_bid, max_yesterday_bid * 1.1 + 10) # Significantly outbid
        elif num_water_slots < num_competitors: # Some will lose, but more than one slot available
            base_bid = max(base_bid, max_yesterday_bid + 5) # Slightly outbid max
        else: # Fallback, should be covered by previous if/elif for tight supply
            base_bid = max(base_bid, avg_yesterday_bid * 1.1)
    else: # Supply is abundant or sufficient for everyone
        # Can afford to bid lower, try to save budget
        base_bid = min(base_bid, avg_yesterday_bid * 0.9 if avg_yesterday_bid > 0 else DAILY_SALARY * 0.4)
        # If supply is very abundant (e.g., double the need), bid even lower
        if num_water_slots >= num_competitors * 2:
            base_bid = min(base_bid, DAILY_SALARY * 0.3)

    # Adjust based on my HP
    if my_hp <= 4: # Getting a bit low, need to prioritize water
        base_bid = max(base_bid, DAILY_SALARY * 0.75) # Increase bid to secure water
    elif my_hp >= 8 and not is_supply_tight: # Good HP, and supply is not tight, can afford to save more
        base_bid = min(base_bid, DAILY_SALARY * 0.4) # Try to save

    # Adjust for late game
    if current_day >= EPISODE_DAYS - 2: # Last 2 days, push for survival/win
        base_bid = max(base_bid, DAILY_SALARY * 0.9) # Be more aggressive
        if my_hp <= 3: # Very desperate in late game
            base_bid = max(base_bid, DAILY_SALARY * 1.2)

    # Final bid calculation: Ensure within budget and positive
    final_bid = max(1.0, base_bid)

    # Crucially, if my budget is too low to meet the target bid and I'm not desperate,
    # it's better to bid a conservative amount, hoping to get lucky or save budget for next day.
    if my_budget < final_bid and my_budget < DAILY_SALARY * 0.8: 
        if my_hp > 2 and my_no_water_days == 0: # Not desperate, conserve budget
            final_bid = min(my_budget, DAILY_SALARY * 0.3)
        else: # Still desperate, bid everything available
            final_bid = my_budget
    else:
        final_bid = min(my_budget, final_bid)

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    remaining_days = EPISODE_DAYS - day_context['day']

    # Base bid strategy
    bid = DAILY_SALARY * 0.5

    # --- Health-based adjustments ---
    if my_status['hp'] <= 2: # Critical health
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4 and my_status['no_water_days'] > 0: # Low health, missed water yesterday
        bid = DAILY_SALARY * 0.8
    elif my_status['hp'] <= 6 and remaining_days <= 3: # End game push
        bid = DAILY_SALARY * 0.75

    # --- Opponent-based adjustments (using previous_trace) ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents were very aggressive yesterday
        if max_prev_bid > DAILY_SALARY * 0.8:
            if my_status['hp'] > 5: # If I have decent HP, I can afford to not win every day
                bid = min(bid, DAILY_SALARY * 0.6) # Try to save
            else: # Must win
                bid = max(bid, max_prev_bid + 1.0) # Bid slightly above
        # If opponents were moderately aggressive
        elif max_prev_bid > DAILY_SALARY * 0.5:
            bid = max(bid, avg_prev_bid * 1.05) # Try to slightly outbid average
        # If opponents were not very aggressive
        else:
            if my_status['hp'] > 7: # If HP is good, try to get it cheaper
                bid = min(bid, DAILY_SALARY * 0.4)
            else: # Ensure water if not too risky
                bid = max(bid, DAILY_SALARY * 0.45)

    # --- Supply-based adjustments ---
    MIN_SUPPLY = 15.0 # From meta-round state
    MAX_SUPPLY = 25.0 # From meta-round state

    # If supply is very scarce (only enough for one or two players)
    if day_context['supply'] < WATER_REQ * 2: # Very high competition if multiple players need water
        if num_alive_opponents >= 1:
            if my_status['hp'] <= 6: # If health is not great, bid very high
                bid = max(bid, DAILY_SALARY * 0.9)
            else: # If health is good, still need to be competitive
                bid = max(bid, DAILY_SALARY * 0.7)
    # If supply is scarce (close to min_supply but more than enough for one)
    elif day_context['supply'] <= MIN_SUPPLY + 2.0: # e.g., 15, 16, 17
        if num_alive_opponents >= 1: # If there's competition
            bid = max(bid, DAILY_SALARY * 0.65) # Increase bid
    # If supply is abundant (close to max_supply)
    elif day_context['supply'] >= MAX_SUPPLY - 2.0: # e.g., 23, 24, 25
        if my_status['hp'] > 5: # If HP is good, try to save
            bid = min(bid, DAILY_SALARY * 0.4)
        else: # Still need water, but maybe cheaper
            bid = max(bid, DAILY_SALARY * 0.5)


    # Ensure bid doesn't exceed budget and is positive
    bid = min(bid, my_status['budget'])
    bid = max(0.1, bid) # Minimum bid to ensure participation

    # Final check for critical budget situations, especially late game
    if my_status['budget'] < DAILY_SALARY * 0.5 and remaining_days <= 2:
        bid = my_status['budget']

    return float(bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    # Given supply range [15, 25] and WATER_REQ 13, there's always only 1 full slot.
    # This means competition is extremely high for the single available water.

    # Identify serious competitors and their yesterday's bids
    # Based on meta-round context, David bids 0, Bob bids low and dies early.
    # Alex and Eric are the main competitors.
    highest_opponent_prev_bid = 0.0
    for opp_id, opp in opponents_status.items():
        if opp['alive'] and opp_id not in ["David", "Bob"]:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                highest_opponent_prev_bid = max(highest_opponent_prev_bid, prev['bid'])

    # Determine a base competitive bid
    # This base is set to be competitive against Alex's average bid
    base_competitive_bid = DAILY_SALARY * 0.8 # 120.0

    # Target bid is at least the base, or slightly above the highest opponent's previous bid
    target_bid = max(base_competitive_bid, highest_opponent_prev_bid + 2.0)

    # Adjust bid based on my HP for increased aggression when needed
    if my_status['hp'] <= 2: # Critical HP
        target_bid = max(target_bid, DAILY_SALARY * 0.98) # 147.0 - Very aggressive
    elif my_status['hp'] <= 4: # Low HP
        target_bid = max(target_bid, DAILY_SALARY * 0.90) # 135.0 - Aggressive

    # Consider remaining days (late game push)
    remaining_days = EPISODE_DAYS - day_context['day'] + 1
    if remaining_days <= 3 and my_status['budget'] > target_bid and my_status['hp'] > 0:
        # If we are near the end and have budget, push harder to secure water
        target_bid = max(target_bid, DAILY_SALARY * 0.95) # 142.5

    # Final bid calculation
    final_bid = target_bid

    # If HP is critical, allow bidding up to current budget to survive
    if my_status['hp'] <= 2:
        final_bid = min(my_status['budget'], final_bid)
    else:
        # Otherwise, cap bid at daily salary for sustainability
        final_bid = min(my_status['budget'], final_bid, DAILY_SALARY * 1.0)

    # Ensure a minimum bid if budget allows, to avoid accidental 0 bid when competitive
    if final_bid < 10.0 and my_status['budget'] >= 10.0:
        final_bid = 10.0

    # Ensure bid is always within budget (final check)
    final_bid = min(final_bid, my_status['budget'])

    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid if no opponents
    if not alive_opponents:
        # If no competition, bid a reasonable amount to secure water without overspending.
        # 0.4 * 150 = 60. This covers 13 units at ~4.6 per unit.
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    current_supply = day_context['supply']
    current_day = day_context['day']

    # Desperation logic: high bid if HP is critically low or multiple days without water
    is_desperate = my_status['hp'] <= 3 or my_status['no_water_days'] >= 2
    # Also desperate if it's late in the game and I'm not fully healthy
    if current_day >= EPISODE_DAYS - 2 and my_status['hp'] < WATER_REQ:
        is_desperate = True

    if is_desperate:
        # Bid very aggressively to survive (0.95 * 150 = 142.5)
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # Analyze opponent's previous bids to gauge competition
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Initialize bid with a moderate value (0.5 * 150 = 75)
    bid = DAILY_SALARY * 0.5

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Adjust bid based on opponent's highest previous bid
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents bid very high (>=120)
            bid = max(bid, highest_prev_bid * 1.05) # Slightly outbid or match high bids
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # Opponents bid moderately (>=90)
            bid = max(bid, highest_prev_bid * 0.95) # Bid slightly below or similar
        else: # Opponents bid low (<90)
            bid = max(DAILY_SALARY * 0.3, highest_prev_bid * 0.8) # Bid conservatively, but at least 45

    # Further adjust bid based on current supply vs total water demand
    total_opponent_water_demand = sum(o['water_requirement'] for o in alive_opponents)
    total_system_water_demand = total_opponent_water_demand + WATER_REQ

    # If supply is tight compared to total demand, increase bid
    if current_supply < total_system_water_demand * 0.8: # Supply is less than 80% of demand
        bid = max(bid, DAILY_SALARY * 0.7) # Increase to 105
    elif current_supply < total_system_water_demand * 1.2: # Supply is somewhat tight (between 80% and 120% of demand)
        bid = max(bid, DAILY_SALARY * 0.6) # Increase to 90
    else: # Supply is abundant (more than 120% of demand)
        bid = min(bid, DAILY_SALARY * 0.4) # Decrease to 60

    # Ensure the final bid does not exceed budget
    final_bid = min(my_status['budget'], bid)
    
    # If I need water (HP not full) and the calculated bid is too low, ensure a minimum threshold bid
    # This prevents bidding too low and losing water when it's needed, even if competition seems low
    if my_status['hp'] < WATER_REQ and final_bid < DAILY_SALARY * 0.3: # If bid is less than 45
        final_bid = max(final_bid, DAILY_SALARY * 0.3) # Ensure at least 45

    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid conservatively to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Initialize bid with a base value
    bid = DAILY_SALARY * 0.55 

    # --- Adjust bid based on my HP --- 
    # The lower my HP, the more aggressively I should bid to survive.
    if my_status['hp'] <= 2: # Very critical HP
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Critical HP
        bid = max(bid, DAILY_SALARY * 0.8)
    elif my_status['hp'] <= 6: # Low HP
        bid = max(bid, DAILY_SALARY * 0.7)

    # --- Adjust bid based on remaining days (end game strategy) ---
    # Bid more aggressively as the game approaches its end.
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: # Last 2 days, bid very aggressively
        bid = max(bid, DAILY_SALARY * 0.9)
    elif remaining_days <= 4: # Last 4 days, increase aggression
        bid = max(bid, DAILY_SALARY * 0.75)

    # --- Analyze opponents' previous bids, especially Eric's --- 
    # Eric is identified as a strong, high-bidding opponent from meta-round context.
    yesterday_bids = []
    eric_prev_bid = 0.0
    eric_alive = False

    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
            if opp_id == 'Eric':
                eric_alive = True
                if prev and prev.get('bid') is not None:
                    eric_prev_bid = prev['bid']

    # React specifically to Eric's previous bid if he's alive and bid high
    if eric_alive and eric_prev_bid > 0:
        if eric_prev_bid >= DAILY_SALARY * 0.7: # Eric was aggressive
            bid = max(bid, eric_prev_bid + 2.0) # Try to outbid him by a small margin
        elif eric_prev_bid >= DAILY_SALARY * 0.5: # Eric was moderately aggressive
            bid = max(bid, eric_prev_bid + 1.0)

    # React to the highest overall previous bid from any alive opponent
    if yesterday_bids:
        highest_prev_bid_overall = max(yesterday_bids)
        if highest_prev_bid_overall > bid: # If some opponent bid higher than my current calculated bid
            bid = highest_prev_bid_overall + 1.5 # Slightly outbid them to secure water

    # --- Adjust bid based on supply scarcity ---
    # If the available water supply is low, competition will be higher.
    # For Cindy (WATER_REQ=13), supply <= 15 is very tight (only enough for one player).
    if day_context['supply'] <= WATER_REQ + 2: # e.g., supply 15 means 13 for me, 2 left, highly contested
        bid = max(bid, DAILY_SALARY * 0.85)
    elif day_context['supply'] <= WATER_REQ * 2 - 2: # e.g., supply 24 means 13 for me, 11 left, not enough for two full requirements
        bid = max(bid, DAILY_SALARY * 0.7)

    # --- Final bid calculation and budget constraint ---
    # The bid cannot exceed the current budget.
    final_bid = min(my_status['budget'], bid)

    # Ensure a minimum bid of 1.0 if budget allows and water is needed (HP not full).
    # Assuming 'full HP' means having 10 HP for an EPISODE_DAYS=10 game.
    if my_status['budget'] > 0 and my_status['hp'] < EPISODE_DAYS:
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
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    current_day = day_context['day']
    days_remaining = EPISODE_DAYS - current_day

    # If no opponents are alive, bid conservatively to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Determine bid strategy based on my status and opponent behavior
    
    # Critical HP (will die if no water) or very late in the game, must secure water
    if my_status['hp'] <= WATER_REQ or days_remaining <= 1:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    # If HP is moderately low, or it's the second to last day, bid high
    if my_status['hp'] <= WATER_REQ + 5 or days_remaining <= 2:
        if highest_prev_bid > DAILY_SALARY * 0.7:
            return min(my_status['budget'], highest_prev_bid + 5)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.8)

    # General bidding strategy, reacting to opponent's highest previous bid
    if highest_prev_bid >= DAILY_SALARY * 0.8:
        if my_status['hp'] > WATER_REQ + 5:
            return min(my_status['budget'], DAILY_SALARY * 0.4)
        else:
            return min(my_status['budget'], highest_prev_bid + 2)

    elif highest_prev_bid > DAILY_SALARY * 0.5:
        return min(my_status['budget'], highest_prev_bid + 1.5)
    
    else: # Opponents bid low or no previous bids, consider supply
        supply = day_context['supply']
        total_opp_water_needed = sum(o['water_requirement'] for o in alive_opponents)
        
        if supply >= WATER_REQ + total_opp_water_needed:
            return min(my_status['budget'], DAILY_SALARY * 0.2)
        elif supply >= WATER_REQ:
            return min(my_status['budget'], DAILY_SALARY * 0.5)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.7)

    return min(my_status['budget'], DAILY_SALARY * 0.5)
"""
