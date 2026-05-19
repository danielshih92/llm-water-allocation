# ============================================================
# Experiment: exp_113
# Agent: Cindy
# Source: exp_113
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid a very low amount to secure water cheaply.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1) # Bid 15

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Determine base bid based on my HP and general competitive pressure
    bid = DAILY_SALARY * 0.55 # Default base bid (82.5)

    if my_status['hp'] <= 2: # Critical HP
        bid = DAILY_SALARY * 0.95 # 142.5
        if highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid + 5) # Outbid previous high aggressively
    elif my_status['hp'] == 3: # Low HP
        bid = DAILY_SALARY * 0.8 # 120
        if highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid + 2) # Outbid previous high moderately
    else: # Stable HP (> 3)
        # If previous bids were high, still be competitive but not desperate
        if highest_prev_bid >= DAILY_SALARY * 0.8: # If previous high bid was >= 120
            bid = DAILY_SALARY * 0.75 # 112.5
            if highest_prev_bid > 0:
                bid = max(bid, highest_prev_bid + 1) # Slightly outbid
        elif highest_prev_bid > 0: # If previous bids existed but were moderate/low
            bid = max(bid, highest_prev_bid + 1) # Slightly outbid
        # Otherwise, use default bid (DAILY_SALARY * 0.55)

    # Final check: Ensure bid does not exceed available budget
    return min(my_status['budget'], bid)
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
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if my_status['hp'] <= 3:
        current_bid = DAILY_SALARY * 0.98 
    elif my_status['hp'] <= 5:
        current_bid = DAILY_SALARY * 0.90
    elif my_status['hp'] <= 7:
        current_bid = DAILY_SALARY * 0.85
    else:
        current_bid = DAILY_SALARY * 0.75 
    
    if day_context['day'] >= EPISODE_DAYS - 3:
        current_bid = max(current_bid, DAILY_SALARY * 0.95)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            current_bid = max(current_bid, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            current_bid = max(current_bid, highest_prev_bid + 3)
        else:
            current_bid = max(current_bid, highest_prev_bid + 1)
            if my_status['hp'] < 10: 
                current_bid = max(current_bid, DAILY_SALARY * 0.7)

    final_bid = min(my_status['budget'], max(0.0, current_bid))
    
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    serious_opponents = []
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev_trace = opp.get('previous_trace', {})
            opp_bid_yesterday = prev_trace.get('bid', 0.0)
            
            # An opponent is serious if they have a water requirement or bid > 0 yesterday
            if opp.get('water_requirement', 0) > 0 or opp_bid_yesterday > 0:
                serious_opponents.append(opp)
                if opp_bid_yesterday > 0:
                    yesterday_bids.append(opp_bid_yesterday)

    num_serious_opponents = len(serious_opponents)

    # Calculate how many agents can get water
    capacity = int(current_supply // WATER_REQ)

    # --- Urgency-based Bids ---
    # If HP is critical or missed water yesterday, bid very aggressively
    if my_hp <= 2 or my_no_water_days >= 1:
        if yesterday_bids:
            max_yesterday_bid = max(yesterday_bids)
            return min(my_budget, max(DAILY_SALARY * 1.1, max_yesterday_bid + 5))
        return min(my_budget, DAILY_SALARY * 1.1)

    # --- Strategic Bidding based on Competition and Supply ---

    # Case 1: No serious opponents or abundant supply
    if num_serious_opponents == 0 or capacity >= num_serious_opponents + 1:
        # Bid low to save money, but not 0 to avoid being outbid by a default bid of 1
        return min(my_budget, 10)

    # Case 2: Tight competition (capacity is limited)
    # Sort yesterday's bids in descending order to find competitive thresholds
    sorted_yesterday_bids = sorted(yesterday_bids, reverse=True)

    target_bid = DAILY_SALARY * 0.8 # Default competitive bid

    if capacity == 1: # Only one winner possible
        if sorted_yesterday_bids:
            # Need to beat the highest bid
            target_bid = max(target_bid, sorted_yesterday_bids[0] + 5)
        else:
            # No competitive bids from yesterday, assume high competition
            target_bid = DAILY_SALARY * 1.05
    elif capacity > 1 and capacity <= num_serious_opponents:
        # Multiple winners, but not everyone can win.
        # We need to be among the top 'capacity' bidders.
        # So, we need to beat the bid at index `capacity - 1` (0-indexed)
        target_index = int(capacity) - 1 # CRITICAL INDEX RULE: int() conversion
        if len(sorted_yesterday_bids) > target_index:
            threshold_bid = sorted_yesterday_bids[target_index]
            target_bid = max(target_bid, threshold_bid + 5)
        else:
            # Not enough data for this specific capacity, or all bids were low.
            # Use a generally competitive bid.
            target_bid = DAILY_SALARY * 0.9

    # --- Final Bid Adjustment ---
    # Don't bid excessively if HP is very high and it's not the last day
    if my_hp > 7 and current_day < EPISODE_DAYS - 2:
        # If I'm doing very well, I can be slightly less aggressive
        target_bid = min(target_bid, DAILY_SALARY * 1.0) # Cap at salary if not urgent

    # Ensure bid is at least 1 and within budget
    return min(my_budget, max(1, target_bid))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
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

    # --- Base Bid Strategy ---
    # Based on meta-round context, high bids are necessary for survival.
    # Start with a strong default bid.
    target_bid = DAILY_SALARY * 0.85 # Strong default, considering Alex's average was 112.6, Eric's 159.0

    # Increase bid if health is critical or no water days
    if my_no_water_days > 0 or my_hp <= 2:
        target_bid = DAILY_SALARY * 0.98 # Max bid for survival
    elif my_hp <= 4:
        target_bid = DAILY_SALARY * 0.90 # High bid for low health

    # --- Opponent Reaction ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace')
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        lowest_prev_bid = min(yesterday_bids)
        
        # If supply is tight (e.g., only enough for one or two agents), and opponents bid high
        # We need to outbid them to secure water.
        # Check if current_supply is less than twice my water requirement
        if current_supply < WATER_REQ * 2 and highest_prev_bid > DAILY_SALARY * 0.7:
            target_bid = max(target_bid, highest_prev_bid + 1.0) # Try to slightly outbid the highest
        
        # If opponents generally bid low and I'm healthy, try to save money
        elif lowest_prev_bid < DAILY_SALARY * 0.6 and my_hp > 5:
            target_bid = min(target_bid, lowest_prev_bid + 5.0) # Bid slightly above the lowest to win cheap

    # --- Final Adjustments ---
    # Cap bid at current budget
    final_bid = min(target_bid, my_budget)

    # Ensure bid is positive
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
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Determine base bid, starting with a value reflecting daily water need
    base_bid = DAILY_SALARY * 0.5 # 75

    # How many people can theoretically get water?
    potential_winners = int(day_context['supply'] // WATER_REQ)
    num_total_competitors = num_alive_opponents + 1 # Myself + opponents

    if potential_winners < num_total_competitors:
        # High competition: supply is less than demand for water
        if my_status['hp'] <= 2:
            # Very aggressive bid if HP is critically low
            base_bid = max(base_bid, max_yesterday_bid + 5, DAILY_SALARY * 0.95)
        elif my_status['hp'] <= 4:
            # Aggressive bid if HP is low
            base_bid = max(base_bid, max_yesterday_bid + 3, DAILY_SALARY * 0.8)
        else:
            # Competitive, but I have some HP buffer
            base_bid = max(base_bid, max_yesterday_bid + 1, DAILY_SALARY * 0.6)
            # Ensure a floor for competitive scenarios
            base_bid = max(base_bid, DAILY_SALARY * 0.4)
    else:
        # Lower competition: supply is enough for all or more
        if my_status['hp'] <= 2:
            # Still need water, but can be slightly less aggressive
            base_bid = max(max_yesterday_bid * 1.05, DAILY_SALARY * 0.7)
        else:
            # Save money, bid below max_yesterday_bid if it exists, but ensure a floor
            base_bid = max(DAILY_SALARY * 0.25, max_yesterday_bid * 0.9)
            # Cap it to avoid overbidding if max_yesterday_bid was high but unnecessary
            base_bid = min(base_bid, DAILY_SALARY * 0.5)

    # Final check: Don't bid more than budget and ensure bid is positive
    final_bid = max(1.0, min(my_status['budget'], base_bid))

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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents are alive, bid minimum to secure water
    if num_alive_opponents == 0:
        return max(1.0, min(my_budget, DAILY_SALARY * 0.1))

    # Determine a base bid based on my urgency
    if my_hp <= 2 or my_no_water_days > 0:
        # Critical state: high urgency
        my_urgency_bid = DAILY_SALARY * 0.95
    elif my_hp <= 5:
        # Low HP: medium-high urgency
        my_urgency_bid = DAILY_SALARY * 0.85
    elif current_day >= EPISODE_DAYS * 0.7:
        # Late game: increasing urgency
        my_urgency_bid = DAILY_SALARY * 0.75
    else:
        # Healthy, early/mid game: moderate urgency
        my_urgency_bid = DAILY_SALARY * 0.6

    # Analyze opponents' previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    opponent_influenced_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were aggressive, I need to be more aggressive
        if highest_prev_bid >= DAILY_SALARY * 0.8: # High bids from opponents (like Eric/Alex)
            opponent_influenced_bid = highest_prev_bid + (DAILY_SALARY * 0.05) # Outbid slightly
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderate bids
            opponent_influenced_bid = highest_prev_bid + (DAILY_SALARY * 0.02) # Outbid slightly
        else: # Low bids (like Bob)
            opponent_influenced_bid = highest_prev_bid + 1.0 # Just barely outbid
    else:
        # If no previous bids from active opponents, rely on my urgency bid
        # The max() call below will ensure my_urgency_bid is used.
        opponent_influenced_bid = 0.0 # Will be overridden by my_urgency_bid via max()

    # Combine my urgency with opponent behavior
    # Always aim for at least my urgency bid, but also react to high opponent bids
    final_bid = max(my_urgency_bid, opponent_influenced_bid)

    # Ensure the bid does not exceed current budget
    final_bid = min(final_bid, my_budget)

    # Ensure bid is at least 1.0 to participate
    final_bid = max(1.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid a small amount to get water
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Base bid strategy
    bid = DAILY_SALARY * 0.6 

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP
        bid = DAILY_SALARY * 0.8
    elif my_status['hp'] >= 8: # High HP, can be a bit more conservative
        bid = DAILY_SALARY * 0.55

    # Adjust bid based on day progress and remaining budget
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 3 and my_status['hp'] > 0: # Nearing end, secure survival
        bid = max(bid, DAILY_SALARY * 0.75)
    
    # If budget is very high, and I'm healthy, I can try to outbid others
    # This also helps to eliminate weaker opponents
    if my_status['budget'] > DAILY_SALARY * 5 and my_status['hp'] >= 5:
        bid = max(bid, DAILY_SALARY * 0.85)

    # Analyze opponent's previous bids from yesterday's trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest previous bid was very high, it indicates strong competition
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            bid = max(bid, highest_prev_bid + 5) # Bid slightly higher than highest
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderate competition
            bid = max(bid, highest_prev_bid + 2)
        else:
             bid = max(bid, DAILY_SALARY * 0.65) # Ensure a reasonable bid even if others were low

    # If supply is low relative to number of players, increase bid
    # If supply is less than 2*WATER_REQ, competition is high since only one player can reliably get water.
    if day_context['supply'] < 2 * WATER_REQ and num_alive_opponents > 0:
        bid = max(bid, DAILY_SALARY * 0.7)

    # Ensure bid does not exceed budget
    bid = min(bid, my_status['budget'])

    # Ensure bid is at least a minimum sensible amount if budget allows, to avoid bidding 0 if budget is very low but not 0
    if bid < DAILY_SALARY * 0.1 and my_status['budget'] > DAILY_SALARY * 0.1:
        bid = DAILY_SALARY * 0.1
    
    # If budget is too low to even make a minimal bid, bid whatever is left
    if my_status['budget'] <= 0:
        return 0.0
    
    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From Current Meta-Round State

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no active opponents, bid low to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    remaining_days = EPISODE_DAYS - day_context['day'] + 1
    if remaining_days <= 0:
        remaining_days = 1

    # Base bid: a solid competitive bid, aiming for profit but ready to compete
    base_bid = DAILY_SALARY * 0.6 # Starting at 90

    # Collect previous bids from alive opponents to gauge competition
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and prev['bid'] > 0:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Adjust bid based on opponent's previous bids
    if highest_prev_bid > base_bid * 0.8: # If highest previous bid is significant
        # Bid slightly above the highest previous bid to outcompete
        base_bid = max(base_bid, highest_prev_bid + (DAILY_SALARY * 0.05))
        
    # Adjust bid based on my HP (desperation factor)
    if my_status['hp'] <= 2: # Critical HP, need water desperately
        base_bid = max(base_bid, DAILY_SALARY * 0.95) # Bid very high
    elif my_status['hp'] <= 4: # Low HP, need water
        base_bid = max(base_bid, DAILY_SALARY * 0.8) # Bid high

    # Adjust bid based on supply scarcity and number of competitors
    # If supply is just enough for one (me), competition is higher.
    if day_context['supply'] <= WATER_REQ + 2 and len(alive_opponents) >= 1: # Tight supply
        if my_status['hp'] <= 3: # Desperate
            base_bid = max(base_bid, DAILY_SALARY * 0.9)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.75) # Be competitive

    # Final bid must not exceed my budget
    final_bid = min(base_bid, my_status['budget'])

    # Also, ensure I don't overspend too much relative to my daily salary if not desperate
    if my_status['hp'] > 2 and final_bid > DAILY_SALARY * 1.1:
        final_bid = DAILY_SALARY * 1.1

    # Ensure bid is at least a minimum if I have budget and need water
    if final_bid <= 0 and my_status['budget'] > 0 and my_status['hp'] < EPISODE_DAYS:
        final_bid = min(my_status['budget'], 1.0)

    # Ensure final bid is non-negative
    final_bid = max(0.0, final_bid)

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

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # 1. Extreme Survival Mode: If HP is critically low or missed water yesterday
    if my_hp <= 2 or my_no_water_days >= 1:
        return min(my_budget, DAILY_SALARY * 0.98) # Bid very aggressively (147)

    # 2. End of Game Aggression: Last few days, need to secure win/survival
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_hp <= 3:
        return min(my_budget, DAILY_SALARY * 0.95) # Aggressive (142.5)

    # 3. No Opponents: Bid minimally to save budget
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.3) # Minimal bid (45)

    # 4. Analyze Opponent Bids from Yesterday
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # 5. General Competitive Bidding Strategy
    # Base bid for competitive scenarios, assuming I want water
    base_competitive_bid = DAILY_SALARY * 0.7 # 105

    target_bid = base_competitive_bid

    # If opponents bid high yesterday, try to beat them
    if highest_prev_bid > 0:
        target_bid = max(target_bid, highest_prev_bid + 1) # Bid slightly above highest previous

    # Adjust based on number of opponents and my current HP
    if num_alive_opponents >= 2:
        # High competition. Be more aggressive if HP is not super high.
        if my_hp <= 5: # Moderate HP, need to secure water
            target_bid = max(target_bid, DAILY_SALARY * 0.85) # 127.5
        else: # Good HP, can afford to be slightly less aggressive, but still competitive
            target_bid = max(target_bid, DAILY_SALARY * 0.75) # 112.5
    else: # Only one opponent
        if my_hp <= 4: # Lower HP, be more aggressive against single opponent
            target_bid = max(target_bid, DAILY_SALARY * 0.8) # 120
        else: # Good HP, can be more conservative
            target_bid = max(target_bid, DAILY_SALARY * 0.65) # 97.5

    # Ensure the final bid does not exceed current budget and is capped at my daily salary
    final_bid = min(my_budget, target_bid, DAILY_SALARY * 1.0)

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
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1) # Bid minimally if no opponents

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid_suggestion = DAILY_SALARY * 0.6 # Default competitive bid

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        
        # If max opponent bid was high, try to outbid it
        if max_prev_bid >= DAILY_SALARY * 0.8: # e.g., > 120
            bid_suggestion = max(bid_suggestion, max_prev_bid + 5) 
        # If max opponent bid was moderate, bid slightly above it
        elif max_prev_bid >= DAILY_SALARY * 0.5: # e.g., > 75
            bid_suggestion = max(bid_suggestion, max_prev_bid + 2)
        else: # Low bids from opponents
            bid_suggestion = max(bid_suggestion, DAILY_SALARY * 0.5) # Still bid moderately to win

    # Adjust bid based on my HP and day
    if my_hp <= 2: # Critical HP: Must win water
        bid_suggestion = max(bid_suggestion, DAILY_SALARY * 1.1) # Aggressive
        if current_day >= EPISODE_DAYS - 2: # Last few days, bid even more aggressively
            bid_suggestion = max(bid_suggestion, DAILY_SALARY * 1.3)
    elif my_hp <= 4: # Low HP: Need water, but can be slightly less desperate
        bid_suggestion = max(bid_suggestion, DAILY_SALARY * 0.9)
    elif my_hp >= 7 and current_day <= 2: # Healthy HP early game: conserve budget
        bid_suggestion = min(bid_suggestion, DAILY_SALARY * 0.5) # Don't overspend
    else: # Normal HP
        bid_suggestion = max(bid_suggestion, DAILY_SALARY * 0.7) # A bit higher for normal competition

    # Final bid must not exceed budget
    final_bid = min(my_budget, bid_suggestion)

    # Ensure a minimum bid if budget allows, to stay active
    if final_bid < DAILY_SALARY * 0.1 and my_budget > 0:
        final_bid = min(my_budget, DAILY_SALARY * 0.1)
    elif my_budget == 0:
        final_bid = 0.0 # Cannot bid if no budget

    return final_bid
"""
