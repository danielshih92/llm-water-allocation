# ============================================================
# Experiment: exp_045
# Agent: Cindy
# Source: exp_045
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    current_day = day_context['day']
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid percentage of daily salary
    base_bid_percent = 0.5

    # Adjust base bid based on my HP and no_water_days
    if my_hp <= 2 or my_no_water_days >= 1:
        # Critical survival mode
        base_bid_percent = 0.95
    elif my_hp <= 4:
        # High urgency
        base_bid_percent = 0.75
    elif my_hp > 6 and current_day < EPISODE_DAYS * 0.7:
        # Comfortable and early/mid game, can afford to save
        base_bid_percent = 0.35
    else:
        # Moderate HP or late game
        base_bid_percent = 0.55

    # Calculate total water demand from all alive agents (including myself)
    total_demand = WATER_REQ
    for opp in alive_opponents:
        total_demand += opp['water_requirement']

    # Supply pressure factor: higher when supply is low relative to demand
    supply_pressure_factor = 1.0
    if supply < total_demand:
        # Increase bid if supply is less than total demand
        supply_pressure_factor = 1.0 + (total_demand - supply) / total_demand * 0.5
    elif supply > total_demand * 1.5:
        # Decrease bid if supply is very abundant
        supply_pressure_factor = 1.0 - (supply - total_demand * 1.5) / supply * 0.3
    
    # Cap supply_pressure_factor to a reasonable range to prevent extreme values
    supply_pressure_factor = max(0.7, min(1.5, supply_pressure_factor))

    # Adjust bid based on number of opponents (competition level)
    opponent_factor = 1.0
    if num_alive_opponents >= 3:
        opponent_factor = 1.2 # More competition, bid higher
    elif num_alive_opponents == 2:
        opponent_factor = 1.1
    elif num_alive_opponents == 1:
        opponent_factor = 1.0
    else: # No opponents
        opponent_factor = 0.8 # No competition, can bid lower

    # Combine all factors to get a calculated bid
    calculated_bid = DAILY_SALARY * base_bid_percent * supply_pressure_factor * opponent_factor

    # Determine a minimum bid based on urgency
    min_bid = 1.0 # Absolute minimum bid
    if my_hp <= 2:
        min_bid = DAILY_SALARY * 0.7 # If critical, ensure a high minimum bid
    elif my_hp <= 4:
        min_bid = DAILY_SALARY * 0.4
    else:
        min_bid = DAILY_SALARY * 0.1 # General minimum to stay competitive

    # The final bid is the maximum of the calculated bid and the minimum required bid
    final_bid = max(min_bid, calculated_bid)

    # Ensure bid does not exceed available budget
    final_bid = min(final_bid, my_budget)

    # Ensure bid is at least 1.0 (to avoid zero bids if not explicitly allowed or desired)
    final_bid = max(1.0, final_bid)

    return round(final_bid, 2)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    DAYS_IN_EPISODE = 10

    # 1. Determine my base bid aggressiveness based on my HP and day
    target_bid = DAILY_SALARY * 0.75 # Default moderate bid

    # Adjust based on my HP
    if my_status['hp'] <= 2:
        target_bid = DAILY_SALARY * 0.98 # Desperate
    elif my_status['hp'] <= 4:
        target_bid = DAILY_SALARY * 0.9 # Very high
    elif my_status['hp'] >= 8:
        target_bid = DAILY_SALARY * 0.65 # Healthy, can be less aggressive

    # Adjust based on remaining days (become more aggressive towards the end)
    remaining_days = DAYS_IN_EPISODE - day_context['day']
    if remaining_days <= 2: # Last 2 days
        target_bid = max(target_bid, DAILY_SALARY * 0.95)
    elif remaining_days <= 4: # Last 4 days
        target_bid = max(target_bid, DAILY_SALARY * 0.85)

    # 2. Analyze opponents' previous bids, specifically Bob
    bob_bid_yesterday = 0.0
    bob_alive = False
    
    for opp_id, opp in opponents_status.items():
        if opp_id == "Bob":
            bob_alive = opp['alive']
            if bob_alive:
                prev = opp.get('previous_trace', {})
                if prev and prev.get('bid') is not None:
                    bob_bid_yesterday = prev['bid']
            break # Found Bob, no need to iterate further

    # Count how many agents (including me) are actively competing for water
    alive_opponents_count = sum(1 for opp in opponents_status.values() if opp['alive'])
    num_potential_buyers = alive_opponents_count + 1 # Myself + alive opponents

    # 3. Adjust bid based on Bob's previous behavior and competition level
    if num_potential_buyers == 1: # I am the only one left
        # Water is plentiful for me, bid just enough to secure it.
        target_bid = min(target_bid, DAILY_SALARY * 0.1) # Bid very low if no competition
    else: # There are other competitors, water is scarce relative to demand (given WATER_REQ and supply range)
        if bob_alive and bob_bid_yesterday > 0:
            if my_status['hp'] <= 5: # I need water to survive
                # Try to outbid Bob, but cap it slightly above my daily salary if desperate
                target_bid = max(target_bid, min(DAILY_SALARY * 1.05, bob_bid_yesterday + 5))
            else: # I'm healthy, can afford to lose a round if Bob overbids
                # Be competitive but slightly lower than Bob, hoping he overbids or I still win
                target_bid = max(target_bid, bob_bid_yesterday * 0.95)
        # If Bob isn't alive or didn't bid, and there are other competitors, stick to my base aggressive bid
    
    # Cap the bid at my current budget
    final_bid = min(my_status['budget'], target_bid)

    # Ensure bid is at least 1.0 if I need water and have budget
    # If I have 0 HP, I'm already dead, no need to bid.
    if final_bid <= 0.0 and my_status['budget'] > 0 and my_status['hp'] > 0:
        final_bid = 1.0
    
    # Ensure bid is not negative
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
    EPISODE_DAYS = 10 # From meta-round state

    current_day = day_context['day']
    current_supply = day_context['supply']

    # Base bid: a solid bid to be competitive
    bid = DAILY_SALARY * 0.85 # 127.5

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no active opponents, bid minimally to save budget
    if not alive_opponents:
        return max(0.1, min(my_status['budget'], DAILY_SALARY * 0.1))

    # --- Adjust bid based on opponent's previous bids ---
    # Consider only "strong" opponents who are likely to compete for water.
    # Based on meta-round context, Eric, Alex, David are strong. Bob is weak.
    strong_opponent_prev_bids = []
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive'] and opp_id != "Bob": # Exclude Bob as he's consistently weak
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                strong_opponent_prev_bids.append(prev['bid'])

    if strong_opponent_prev_bids:
        highest_prev_bid = max(strong_opponent_prev_bids)
        # If the highest previous bid was very high (e.g., above my daily salary)
        if highest_prev_bid >= DAILY_SALARY * 1.0: # Eric often bids this high
            # If my HP is critical, I must win, so bid higher than them.
            if my_status['hp'] <= 3:
                bid = max(bid, highest_prev_bid + 15) # Aggressively outbid
            # If my HP is okay, but I still need water, slightly outbid or match.
            else:
                bid = max(bid, highest_prev_bid + 5) # Slightly outbid

        # If previous bids were moderate (below my daily salary, but still competitive)
        elif highest_prev_bid >= DAILY_SALARY * 0.7:
            bid = max(bid, highest_prev_bid + 10) # Ensure I win against moderate bids

    # --- Adjust bid based on my HP ---
    if my_status['hp'] <= 2: # Very low HP, desperate state
        bid = max(bid, DAILY_SALARY * 1.8) # Bid very high, almost 2x salary
    elif my_status['hp'] <= 4: # Low HP, need water to recover
        bid = max(bid, DAILY_SALARY * 1.3)
    elif my_status['no_water_days'] > 0: # Missed water yesterday, implies I need to be more aggressive today
        bid = max(bid, DAILY_SALARY * 1.1)

    # --- Adjust bid based on supply scarcity and number of competitors ---
    # My WATER_REQ is 13.
    # If supply is very low (e.g., 15-18) and there are multiple strong opponents, competition is high.
    if current_supply <= WATER_REQ + 5: # Supply is 13 to 18
        if num_alive_opponents >= 2: # Multiple strong opponents
            bid = max(bid, DAILY_SALARY * 1.25)
        elif num_alive_opponents == 1: # One strong opponent
            bid = max(bid, DAILY_SALARY * 1.1)
    elif current_supply <= WATER_REQ + 2: # Supply is 13 to 15 (very scarce for others)
        if num_alive_opponents >= 1:
            bid = max(bid, DAILY_SALARY * 1.4) # Push hard

    # --- End-game strategy ---
    # In the last few days, be more aggressive to secure survival or win.
    days_remaining = EPISODE_DAYS - current_day
    if days_remaining <= 2: # Last 2 days
        bid = max(bid, DAILY_SALARY * 1.5)
        if my_status['hp'] <= 5: # Critical in end game
            bid = max(bid, DAILY_SALARY * 2.0)
    elif days_remaining <= 4: # Last 4 days
        bid = max(bid, DAILY_SALARY * 1.1)

    # Final constraints:
    # 1. Don't bid more than budget.
    # 2. Don't bid excessively high if not necessary (cap at ~2.2x salary based on Eric's max).
    max_affordable_bid = my_status['budget']
    max_strategic_bid = DAILY_SALARY * 2.2 # Allow slightly higher than Eric's max

    final_bid = min(max_affordable_bid, max_strategic_bid, bid)

    # Ensure bid is at least a minimal amount to always participate if budget allows, and not negative.
    return max(0.1, final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimally to save budget
    if not alive_opponents:
        return min(my_current_budget, DAILY_SALARY * 0.1)

    # --- Determine base bid ---
    base_bid = DAILY_SALARY * 0.5 # Default to 75

    # Adjust base bid based on my health and no-water days
    if my_no_water_days >= 1:
        # Desperate for water, bid very high
        base_bid = DAILY_SALARY * 0.95 # 142.5
    elif my_current_hp <= 3:
        # Low HP, need water urgently
        base_bid = DAILY_SALARY * 0.8 # 120
    elif my_current_hp <= 5:
        # Moderately low HP
        base_bid = DAILY_SALARY * 0.65 # 97.5

    # --- Adjust bid based on opponent's previous bids ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        # If max opponent bid was high, bid slightly above it, but not excessively
        # Considering Eric's max_bid (230) and avg_bid (154.5), and David's (193.38, 100.2)
        # A threshold of 0.6 * DAILY_SALARY (90) is reasonable to identify high bidders.
        if max_prev_bid > DAILY_SALARY * 0.6:
            base_bid = max(base_bid, max_prev_bid + 5) # Try to outbid by a small margin
        else:
            # If opponent bids were generally low, try to win with a slightly lower bid
            base_bid = max(base_bid, max_prev_bid + 1)

    # --- Adjust bid based on supply scarcity ---
    # If supply is very low, competition for water is higher
    # If supply is less than 2 * WATER_REQ, it's very competitive.
    if current_supply < WATER_REQ * 2: # e.g., supply 15, WATER_REQ 13. Only one can get water.
        base_bid = max(base_bid, DAILY_SALARY * 0.75) # 112.5 - Increase bid due to scarcity

    # --- Adjust bid for end game ---
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        base_bid = max(base_bid, DAILY_SALARY * 0.9) # Prioritize survival, bid high (135)

    # Ensure bid doesn't exceed current budget
    final_bid = min(my_current_budget, base_bid)

    # Ensure bid is at least 1 to participate (assuming 0 or negative is invalid)
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)
    num_total_competitors = num_alive_opponents + 1 # Including myself

    # Calculate potential water units available for my requirement
    num_water_units_available = int(current_supply // WATER_REQ)

    # Base bid strategy
    base_bid = DAILY_SALARY * 0.5 # Start with a moderate bid

    # Critical HP or no water days -> Bid aggressively
    if my_hp <= 2 or my_no_water_days >= 1:
        base_bid = DAILY_SALARY * 0.95
        # If budget is low but I desperately need water, I might even exceed salary if it's the last few days
        if my_budget < base_bid and current_day >= EPISODE_DAYS - 2:
            base_bid = my_budget # Bid all if it's the very end and I'm desperate

    # High competition scenario (supply is tight for the number of competitors)
    elif num_water_units_available < num_total_competitors:
        if my_hp <= 4: # If HP is a bit low, be more aggressive
            base_bid = DAILY_SALARY * 0.8
        else: # Otherwise, still competitive but not desperate
            base_bid = DAILY_SALARY * 0.65

    # End game pressure
    elif current_day >= EPISODE_DAYS - 2: # Last 2 days
        if my_hp <= 5: # Need water to survive
            base_bid = DAILY_SALARY * 0.9
        else: # Still try to get water, but can be slightly less aggressive
            base_bid = DAILY_SALARY * 0.7

    # Adjust based on yesterday's opponent bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents bid high yesterday, I might need to increase my bid
        if max_yesterday_bid > DAILY_SALARY * 0.7: # Opponents were aggressive
            if my_hp <= 4 or num_water_units_available < num_total_competitors:
                # If I need water or competition is high, bid above their max
                base_bid = max(base_bid, max_yesterday_bid + 5)
            else:
                # Otherwise, stay competitive but don't overpay if not necessary
                base_bid = max(base_bid, avg_yesterday_bid * 1.1)
        elif max_yesterday_bid < DAILY_SALARY * 0.3: # Opponents were conservative
            if my_hp > 5 and num_water_units_available >= num_total_competitors:
                # If I'm healthy and supply is good, try to bid lower
                base_bid = min(base_bid, max_yesterday_bid + 10) # Bid slightly above to win cheaply

    # Ensure bid is not negative or zero if budget is very low, and does not exceed budget
    final_bid = max(1.0, min(my_budget, base_bid))

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

    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_competitors = len(alive_opponents) + 1 # Including myself

    # Determine how many agents can get full water
    num_water_slots = int(current_supply // WATER_REQ)

    # Base bid, slightly above average to compete
    base_bid = DAILY_SALARY * 0.65

    # Collect previous bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    bid = base_bid

    # Adjust bid based on my HP and no_water_days
    if my_status['hp'] <= 2: # Critical HP, must get water
        bid = max(highest_prev_bid + 5, DAILY_SALARY * 1.15) # Bid very aggressively
    elif my_status['hp'] <= 4 and my_status['no_water_days'] > 0: # Low HP and missed water yesterday
        bid = max(highest_prev_bid + 3, DAILY_SALARY * 1.05) # Bid aggressively
    else:
        # Normal bidding logic based on competition
        if num_water_slots >= num_alive_competitors: # Enough water for everyone
            bid = min(DAILY_SALARY * 0.5, highest_prev_bid + 1) # Bid low but ensure getting water
            if highest_prev_bid == 0: # If no previous bids, use base low bid
                bid = DAILY_SALARY * 0.5
        elif num_water_slots == 1: # Only one slot, very high competition
            bid = max(base_bid, highest_prev_bid + 5) # Bid aggressively
            if highest_prev_bid > DAILY_SALARY * 0.9: # Counter very high bids from Alex/Eric/David
                bid = max(highest_prev_bid + 1, DAILY_SALARY * 1.1)
        else: # num_water_slots > 1 but less than num_competitors, some competition
            bid = max(base_bid, highest_prev_bid + 2)
            if highest_prev_bid > DAILY_SALARY * 0.8:
                bid = max(highest_prev_bid + 1, DAILY_SALARY * 1.0)

    # Factor in remaining days. Increase bid towards the end.
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last 2 days, be very aggressive
        bid = max(bid, DAILY_SALARY * 1.1)
    elif remaining_days <= 4: # Last 4 days, be aggressive
        bid = max(bid, DAILY_SALARY * 0.95)

    # Ensure bid doesn't exceed budget
    bid = min(bid, my_status['budget'])

    # Ensure bid is at least a minimal amount to participate if budget allows
    if bid < DAILY_SALARY * 0.1 and my_status['budget'] > DAILY_SALARY * 0.1:
        bid = DAILY_SALARY * 0.1

    # Ensure bid is at least 1.0 to be a valid bid
    bid = max(1.0, bid)

    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_supply = day_context['supply']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid: A fair price for water, adjusted by urgency
    bid_value = DAILY_SALARY * 0.5 # Start with half salary

    # Urgency based on HP
    if my_hp <= 2: # Critical HP
        bid_value = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP
        bid_value = DAILY_SALARY * 0.75
    elif my_no_water_days > 0: # Missed water yesterday
        bid_value = DAILY_SALARY * 0.85
    else: # Healthy HP
        bid_value = DAILY_SALARY * 0.6

    # Adjust for end-game
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_hp <= 2: # Last days, low HP
        bid_value = DAILY_SALARY * 1.0 # Bid full salary or more to survive

    # Opponent analysis from previous_trace
    yesterday_opponent_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_opponent_bids.append(prev_trace['bid'])

    if yesterday_opponent_bids:
        max_prev_bid = max(yesterday_opponent_bids)
        avg_prev_bid = sum(yesterday_opponent_bids) / len(yesterday_opponent_bids)

        # If highest previous bid was significant, react
        if max_prev_bid >= DAILY_SALARY * 0.7: # Opponents are aggressive
            if my_hp <= 3: # I need water, try to outbid
                bid_value = max(bid_value, max_prev_bid + 5)
            else: # I can afford to be slightly less aggressive
                bid_value = max(bid_value, max_prev_bid * 0.95) # Match or slightly undercut
        elif max_prev_bid >= DAILY_SALARY * 0.4: # Moderate competition
            bid_value = max(bid_value, avg_prev_bid + 2)
        else: # Low competition yesterday
            bid_value = max(bid_value, max_prev_bid + 1)

    # Adjust based on supply scarcity vs. demand
    num_possible_winners = int(current_supply // WATER_REQ) # CRITICAL RULE 9: int()
    total_competitors = num_alive_opponents + 1 # Me + alive opponents

    if total_competitors > num_possible_winners: # High competition for water
        if my_hp <= 3:
            bid_value *= 1.1 # Increase bid if desperate
        else:
            bid_value *= 1.05 # Slightly increase if not desperate
    elif total_competitors < num_possible_winners: # Abundant supply relative to demand
        bid_value *= 0.9 # Try to get water cheaper

    # Ensure bid doesn't exceed budget
    final_bid = min(my_budget, bid_value)

    # If I'm very low on HP, bid everything to survive
    if my_hp <= 1 or (remaining_days == 1 and my_hp <= 2):
        final_bid = my_budget

    # If no opponents, bid minimally to save budget
    if num_alive_opponents == 0:
        final_bid = min(my_budget, DAILY_SALARY * 0.1)

    # Ensure bid is non-negative and has a floor if I need water and have budget
    if final_bid <= 0 and my_budget > 0 and my_hp > 0:
        final_bid = min(my_budget, DAILY_SALARY * 0.05)

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

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    # Default bid, adjusted based on situation
    bid = DAILY_SALARY * 0.75

    # Identify strong opponents based on LATEST METAROUND CONTEXT
    strong_opponent_ids = ["Alex", "David"]
    strong_opponents_alive = [
        opp_data for opp_id, opp_data in opponents_status.items()
        if opp_id in strong_opponent_ids and opp_data['alive']
    ]

    # Get the highest bid from strong opponents yesterday
    max_strong_opp_prev_bid = 0
    for opp in strong_opponents_alive:
        prev_trace = opp.get('previous_trace')
        if prev_trace and prev_trace.get('bid') is not None:
            max_strong_opp_prev_bid = max(max_strong_opp_prev_bid, prev_trace['bid'])

    # Adjust bid based on my HP
    if my_hp <= 2: # Critical HP, bid aggressively
        bid = DAILY_SALARY * 0.95
    elif my_hp <= 5: # Low HP
        bid = DAILY_SALARY * 0.85
    elif my_hp >= 8 and current_day < EPISODE_DAYS / 2: # Healthy and early, try to save
        bid = DAILY_SALARY * 0.65

    # Adjust bid based on day (later days are more critical)
    if current_day >= EPISODE_DAYS - 2: # Last few days, push harder
        bid = max(bid, DAILY_SALARY * 0.9)

    # If strong opponents bid high yesterday, try to outbid them
    if max_strong_opp_prev_bid > DAILY_SALARY * 0.6: # Only react if their bid was significant
        bid = max(bid, max_strong_opp_prev_bid + 5) # Try to outbid by a small margin

    # If supply is scarce and multiple strong opponents are alive, increase bid
    # Max supply is 25, WATER_REQ is 13. Only one agent can get full water if supply < 26.
    if len(strong_opponents_alive) >= 1 and current_supply < WATER_REQ * 2: 
        bid = max(bid, DAILY_SALARY * 0.8)

    # Ensure bid does not exceed available budget
    final_bid = min(my_budget, bid)

    # Ensure bid is at least 1 to participate
    final_bid = max(1.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13
    EPISODE_DAYS = 10

    alive_opponents = [agent_id for agent_id, opp_data in opponents_status.items() if opp_data['alive']]
    
    remaining_days = EPISODE_DAYS - day_context['day']

    bid = DAILY_SALARY * 0.5 

    if not alive_opponents:
        if my_status['hp'] > 5:
            return min(my_status['budget'], DAILY_SALARY * 0.3)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.6)

    yesterday_bids = []
    alex_yesterday_bid = 0.0
    
    for agent_id in alive_opponents:
        opp = opponents_status[agent_id]
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            if agent_id == 'Alex':
                alex_yesterday_bid = prev['bid']

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        bid = max(bid, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 5:
        bid = max(bid, DAILY_SALARY * 0.75)

    num_possible_winners = int(day_context['supply'] // WATER_REQ)
    num_alive_competitors = len(alive_opponents) + 1

    if num_alive_competitors > num_possible_winners:
        if highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid + 5.0)
        else:
            bid = max(bid, DAILY_SALARY * 0.6)
            
        if 'Alex' in alive_opponents:
            if day_context['supply'] <= WATER_REQ * 2:
                bid = max(bid, DAILY_SALARY * 0.9)
            else:
                bid = max(bid, DAILY_SALARY * 0.75)
            
            if alex_yesterday_bid > 0:
                bid = max(bid, alex_yesterday_bid + 2.0)
    else:
        bid = min(bid, DAILY_SALARY * 0.6)
        if highest_prev_bid > 0 and highest_prev_bid < DAILY_SALARY * 0.5:
            bid = min(bid, highest_prev_bid + 1.0)

    if remaining_days <= 2:
        bid = max(bid, DAILY_SALARY * 0.98)
    elif remaining_days <= 4:
        bid = max(bid, DAILY_SALARY * 0.85)

    bid = min(bid, my_status['budget'])
    
    if bid == 0.0 and my_status['budget'] > 0 and my_status['hp'] < 10:
        bid = min(my_status['budget'], DAILY_SALARY * 0.1)

    bid = max(0.0, bid)

    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # Assuming this is constant for the meta-round

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If I'm the only agent alive, bid minimum to conserve budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], 1)

    # --- General Strategy for Competition ---

    base_bid_percentage = 0.55 # Starting point for bid as a percentage of daily salary

    # Adjust for perceived scarcity based on total water needed vs. available supply
    total_water_needed_by_alive = (num_alive_opponents + 1) * WATER_REQ
    available_supply = day_context['supply']

    scarcity_factor = 1.0
    if available_supply < total_water_needed_by_alive:
        # Higher scarcity -> higher factor, capped at 1.5 to prevent extreme bids
        scarcity_factor = 2.0 - available_supply / total_water_needed_by_alive
        scarcity_factor = min(scarcity_factor, 1.5)
    else:
        # Abundant supply -> lower factor, min 0.5 to keep a base bid
        scarcity_factor = max(0.5, 1.0 - (available_supply - total_water_needed_by_alive) / available_supply)
    
    base_bid_percentage *= scarcity_factor
    base_bid_percentage = min(base_bid_percentage, 0.95) # Cap upper limit for base bid
    base_bid_percentage = max(base_bid_percentage, 0.3) # Cap lower limit for base bid

    bid = DAILY_SALARY * base_bid_percentage

    # React to yesterday's highest bid from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        # Only consider valid, positive bids from yesterday
        if prev and prev.get('bid') is not None and prev.get('status') != 'error' and prev.get('bid') > 0:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest previous bid was significant, adjust my bid to be competitive
        if highest_prev_bid > DAILY_SALARY * 0.2: # Only react if it's a non-trivial bid
            bid = max(bid, highest_prev_bid + 2) # Aim to slightly beat it
            # More aggressive if my HP is low
            if my_status['hp'] <= WATER_REQ: # Critical HP
                bid = max(bid, highest_prev_bid + 5, DAILY_SALARY * 0.95)
            elif my_status['hp'] <= WATER_REQ * 2: # Low HP
                bid = max(bid, highest_prev_bid + 3, DAILY_SALARY * 0.8)
        else: # Opponents bid very low or 0, try to save money if healthy
            if my_status['hp'] > WATER_REQ * 2: 
                bid = min(bid, DAILY_SALARY * 0.45)
            bid = max(bid, highest_prev_bid + 1) # Still aim to win if possible
    else:
        # No meaningful bids from opponents yesterday. Rely on base bid, adjust for HP.
        if my_status['hp'] <= WATER_REQ: # Critical HP
            bid = max(bid, DAILY_SALARY * 0.9)
        elif my_status['hp'] <= WATER_REQ * 2: # Low HP
            bid = max(bid, DAILY_SALARY * 0.7)
        else:
            bid = max(bid, DAILY_SALARY * 0.5) # Normal healthy bid

    # Final adjustment based on my HP (override if critical for survival)
    if my_status['hp'] <= WATER_REQ: # Critical HP, must get water at almost any cost
        bid = max(bid, DAILY_SALARY * 0.98)
    elif my_status['hp'] <= WATER_REQ * 2: # Low HP, need water
        bid = max(bid, DAILY_SALARY * 0.85)

    # Consider end game: Adjust strategy for the last few days
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days of the episode
        if my_status['hp'] <= WATER_REQ * 2: # Still need water to survive
            bid = max(bid, DAILY_SALARY * 0.95)
        else: # Healthy, try to secure win with minimal cost
            bid = min(bid, DAILY_SALARY * 0.7)

    # Ensure bid is at least 1 to participate
    bid = max(1, bid)

    # Ensure bid does not exceed available budget
    final_bid = min(my_status['budget'], bid)

    # If budget allows, always bid at least 1
    if final_bid == 0 and my_status['budget'] > 0:
        final_bid = 1

    return final_bid
"""
