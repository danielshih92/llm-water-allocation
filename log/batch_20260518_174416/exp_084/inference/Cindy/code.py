# ============================================================
# Experiment: exp_084
# Agent: Cindy
# Source: exp_084
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    CRITICAL_HP_THRESHOLD = 3 # If HP is 3 or less, be desperate
    LOW_HP_THRESHOLD = 5 # If HP is 5 or less, be aggressive

    # Base bid strategy based on my HP and recent water status
    current_bid = 0

    if my_status['hp'] <= CRITICAL_HP_THRESHOLD:
        current_bid = DAILY_SALARY * 0.95 # Very high bid, almost max salary
    elif my_status['hp'] <= LOW_HP_THRESHOLD:
        current_bid = DAILY_SALARY * 0.8 # High bid
    elif my_status['no_water_days'] > 0: # If I missed water yesterday
        current_bid = DAILY_SALARY * 0.7 # Aggressive bid
    else:
        current_bid = DAILY_SALARY * 0.6 # Moderate bid

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Adjust based on opponent behavior (if any)
    if not alive_opponents:
        # No competition, bid low, but ensure I get water if supply is tight
        if day_context['supply'] < WATER_REQ: # If supply is less than my requirement, still need to bid to get it.
            current_bid = DAILY_SALARY * 0.5 # A reasonable bid to secure it
        else:
            current_bid = DAILY_SALARY * 0.1 # Very low bid if ample supply and no competition
    else:
        yesterday_bids = []
        for opp in alive_opponents:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            # If opponents were bidding high, I might need to increase my bid
            # Especially if my current_bid (based on HP) is not already very high.
            if highest_prev_bid >= DAILY_SALARY * 0.7: # Opponents were aggressive
                # If my current_bid isn't already super high, make it higher than theirs
                if my_status['hp'] > LOW_HP_THRESHOLD: # Only if not already desperate
                    current_bid = max(current_bid, highest_prev_bid + 5)
                else: # If desperate, ensure it's at least this high
                    current_bid = max(current_bid, highest_prev_bid + 1)
            elif highest_prev_bid >= DAILY_SALARY * 0.4: # Opponents were moderately aggressive
                 current_bid = max(current_bid, highest_prev_bid + 2)
            else: # Opponents were conservative, try to get it cheaper but still secure
                 current_bid = max(current_bid, highest_prev_bid + 1)
        # If no yesterday_bids (e.g., first day with opponents), current_bid remains HP-based.

    # Final adjustments
    # Ensure bid is at least 1
    current_bid = max(1, current_bid)
    # Ensure bid does not exceed budget
    current_bid = min(my_status['budget'], current_bid)

    return current_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    strong_opponent_ids = ["Alex", "Eric"]
    
    strong_opp_prev_bids = []
    for opp_id in strong_opponent_ids:
        if opp_id in opponents_status and opponents_status[opp_id]['alive']:
            opp_data = opponents_status[opp_id]
            if opp_data.get('previous_trace'):
                prev_bid = opp_data['previous_trace'].get('bid')
                if prev_bid is not None:
                    strong_opp_prev_bids.append(prev_bid)

    highest_strong_opp_bid = 0
    if strong_opp_prev_bids:
        highest_strong_opp_bid = max(strong_opp_prev_bids)

    bid = DAILY_SALARY * 0.7

    if my_hp <= 2:
        if highest_strong_opp_bid > 0:
            bid = max(DAILY_SALARY * 0.9, highest_strong_opp_bid + 5.0)
        else:
            bid = DAILY_SALARY * 0.95
    elif my_hp <= 4:
        if highest_strong_opp_bid > 0:
            bid = max(DAILY_SALARY * 0.8, highest_strong_opp_bid + 2.0)
        else:
            bid = DAILY_SALARY * 0.85
    else:
        if highest_strong_opp_bid > 0:
            bid = max(DAILY_SALARY * 0.6, highest_strong_opp_bid + 1.0)
        else:
            bid = DAILY_SALARY * 0.7

    bid = min(bid, my_budget)
    
    bid = max(1.0, bid)

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

    MIN_BID_FACTOR = 0.1
    LOW_BID_FACTOR = 0.4
    MEDIUM_BID_FACTOR = 0.6
    HIGH_BID_FACTOR = 0.8
    VERY_HIGH_BID_FACTOR = 0.95
    MAX_BID_CAP_FACTOR = 1.2

    bid = DAILY_SALARY * MEDIUM_BID_FACTOR

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * MIN_BID_FACTOR)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and prev.get('status') != 'error':
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    remaining_days = EPISODE_DAYS - day_context['day']

    if my_status['hp'] <= 2:
        bid = DAILY_SALARY * VERY_HIGH_BID_FACTOR
        if highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid + 5.0)
        return min(my_status['budget'], bid, DAILY_SALARY * MAX_BID_CAP_FACTOR)

    if remaining_days <= 2:
        bid = DAILY_SALARY * HIGH_BID_FACTOR
        if highest_prev_bid > DAILY_SALARY * LOW_BID_FACTOR:
            bid = max(bid, highest_prev_bid + 2.0)
        return min(my_status['budget'], bid, DAILY_SALARY * MAX_BID_CAP_FACTOR)

    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * HIGH_BID_FACTOR:
            bid = highest_prev_bid + 1.0
            if my_status['hp'] > 5:
                bid = min(bid, DAILY_SALARY * HIGH_BID_FACTOR + 15.0)
            return min(my_status['budget'], bid, DAILY_SALARY * MAX_BID_CAP_FACTOR)

        elif highest_prev_bid >= DAILY_SALARY * LOW_BID_FACTOR:
            bid = highest_prev_bid + 1.0
            if my_status['hp'] > 5:
                bid = min(bid, DAILY_SALARY * MEDIUM_BID_FACTOR + 10.0)
            else:
                bid = max(bid, DAILY_SALARY * MEDIUM_BID_FACTOR)
            return min(my_status['budget'], bid, DAILY_SALARY * MAX_BID_CAP_FACTOR)
        else:
            if my_status['hp'] >= 5:
                bid = DAILY_SALARY * LOW_BID_FACTOR
            else:
                bid = DAILY_SALARY * MEDIUM_BID_FACTOR
            return min(my_status['budget'], bid)
    else:
        if my_status['hp'] >= 5:
            bid = DAILY_SALARY * LOW_BID_FACTOR
        else:
            bid = DAILY_SALARY * MEDIUM_BID_FACTOR
        return min(my_status['budget'], bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQUIREMENT = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_active_players = len(alive_opponents) + 1

    if num_active_players == 1:
        return min(my_status['budget'], 1.0)

    current_day = day_context['day']
    current_supply = day_context['supply']

    bid = DAILY_SALARY * 0.5

    if my_status['hp'] <= 3:
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5:
        bid = DAILY_SALARY * 0.8
    elif my_status['hp'] >= 8 and my_status['budget'] > DAILY_SALARY * (EPISODE_DAYS - current_day + 1):
        bid = DAILY_SALARY * 0.45

    if current_day >= EPISODE_DAYS - 2:
        bid = max(bid, DAILY_SALARY * 0.9)
    elif current_day >= EPISODE_DAYS * 0.7:
        bid *= 1.1

    highest_prev_bid = 0.0
    eric_prev_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])
            if opp['agent_id'] == 'Eric':
                eric_prev_bid = prev['bid']

    if eric_prev_bid > 0 and eric_prev_bid > DAILY_SALARY * 0.6:
        if my_status['hp'] <= 5 or current_day >= EPISODE_DAYS - 2:
            bid = max(bid, eric_prev_bid * 1.1)
        else:
            bid = max(bid, eric_prev_bid * 1.05)
    elif highest_prev_bid > 0:
        if highest_prev_bid > DAILY_SALARY * 0.4:
            bid = max(bid, highest_prev_bid + 5.0)
        else:
            bid = max(bid, highest_prev_bid + 1.0)

    if current_supply < WATER_REQUIREMENT * 2:
        if num_active_players > 1:
            bid *= 1.15
    elif current_supply < WATER_REQUIREMENT * 2.5:
        if num_active_players > 1:
            bid *= 1.05

    if my_status['no_water_days'] > 0 and my_status['hp'] <= 5:
        bid = max(bid, DAILY_SALARY * 0.95)

    final_bid = min(my_status['budget'], bid)

    if num_active_players > 1 and my_status['budget'] > 0:
        final_bid = max(final_bid, 1.0)

    if my_status['budget'] <= 0:
        final_bid = 0.0

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid a small amount to get water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Calculate supply scarcity factor (1.0 for min supply, 0.0 for max supply)
    supply_range = MAX_SUPPLY - MIN_SUPPLY
    scarcity_factor = 1.0
    if supply_range > 0:
        scarcity_factor = 1.0 - (day_context['supply'] - MIN_SUPPLY) / supply_range

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and prev.get('status') == 'active':
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Determine base bid
    # Ranges from a safe low (e.g., 40% salary) to a competitive high (e.g., 80% salary)
    # The higher the scarcity, the higher the base bid
    base_bid = DAILY_SALARY * (0.4 + 0.4 * scarcity_factor) # Ranges from 60 to 120

    # Adjust bid based on my HP and no_water_days
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        # Critical state: bid very aggressively
        bid = DAILY_SALARY * 0.9 
    else:
        # Normal state: adjust based on opponent's highest bid and scarcity
        if highest_prev_bid > base_bid * 0.9: # If opponents were aggressive
            bid = max(base_bid, highest_prev_bid * 1.05) # Try to slightly outbid, but not less than base
        else:
            bid = base_bid # Default to base bid

    # Ensure bid doesn't exceed budget
    final_bid = min(my_status['budget'], bid)
    final_bid = max(final_bid, 0.0) # Bid cannot be negative

    # Final check for extreme budget situations
    if my_status['budget'] < DAILY_SALARY * 0.5: # Low budget
        if my_status['hp'] <= 2: # Must get water
            final_bid = my_status['budget']
        else: # Can afford to miss water, save budget
            final_bid = min(final_bid, DAILY_SALARY * 0.2) # Bid very low to save

    # If it's the last day, and I have enough budget, bid high to maximize HP
    if day_context['day'] == EPISODE_DAYS - 1 and my_status['budget'] > DAILY_SALARY * 1.5:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.99)

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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # 1. If no opponents, bid just enough to secure water cheaply
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    # 2. Collect yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # 3. Determine a base competitive bid based on opponent history
    target_bid = DAILY_SALARY * 0.6 # Default moderate bid if no history

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        target_bid = highest_prev_bid + 1.0 # Try to beat the highest previous bid

    # 4. Adjust bid based on my HP and no_water_days (priority for survival)
    if my_hp <= 2: # Critical HP, bid very aggressively
        bid = DAILY_SALARY * 0.99
    elif my_status['no_water_days'] > 0: # Missed water yesterday, need it today
        bid = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP, bid aggressively but slightly less than critical
        bid = DAILY_SALARY * 0.9
    else: # Healthy HP, use the calculated competitive bid
        bid = target_bid

    # 5. Adjustment for end of meta-round
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last two days
        if my_hp <= 3: # Desperate to survive
            bid = DAILY_SALARY * 0.99
        elif my_budget >= DAILY_SALARY * 2 and my_hp >= 5: # Healthy and good budget, try to save if possible
            bid = min(bid, DAILY_SALARY * 0.75) # Cap bid to save
        else: # Normal end-game push, ensure competitiveness
            bid = max(bid, DAILY_SALARY * 0.8) # Ensure bid is high enough

    # 6. Final bid must not exceed current budget
    bid = min(bid, my_budget)

    # 7. Ensure bid is at least 1.0 to be considered active
    bid = max(bid, 1.0)

    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta_round_state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # 1. Emergency Bid (Low HP) - Prioritize survival
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # If no opponents, bid conservatively
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    # Initialize bid - start with a reasonable default for moderate competition
    current_bid = DAILY_SALARY * 0.5

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    david_prev_bid = None
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
                if opp_id == 'David':
                    david_prev_bid = prev['bid']

    max_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    # 2. Adjust bid based on highest previous bid from any opponent
    if max_yesterday_bid > 0:
        if max_yesterday_bid >= DAILY_SALARY * 0.7: # High pressure
            current_bid = max(current_bid, max_yesterday_bid * 1.05)
        elif max_yesterday_bid >= DAILY_SALARY * 0.4: # Moderate pressure
            current_bid = max(current_bid, max_yesterday_bid + 5)
        else: # Low pressure, try to win cheaply but don't be too naive
            current_bid = max(current_bid, max_yesterday_bid + 2)
            current_bid = min(current_bid, DAILY_SALARY * 0.6) # Cap to avoid overpaying if others are very low

    # 3. Specific adjustment for David, a known strong player
    if 'David' in opponents_status and opponents_status['David']['alive']:
        if david_prev_bid is not None:
            # If David bid high, ensure we outbid him
            if david_prev_bid >= DAILY_SALARY * 0.6:
                current_bid = max(current_bid, david_prev_bid * 1.03)
            # If David bid low, still maintain a competitive floor against him
            else:
                current_bid = max(current_bid, DAILY_SALARY * 0.55)
        else: # David is alive but no previous bid (e.g., Day 1)
            current_bid = max(current_bid, DAILY_SALARY * 0.6) # Assume David is competitive from Day 1

    # 4. Adjust based on number of active opponents
    if num_alive_opponents >= 3:
        current_bid *= 1.05
    elif num_alive_opponents == 2:
        current_bid *= 1.02

    # Final check: Ensure bid is at least 1.0 and does not exceed current budget
    final_bid = max(1.0, current_bid)
    return min(my_status['budget'], final_bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Calculate effective supply slots (CRITICAL INDEX RULE: int() for clarity, though // on float yields float, int() ensures integer for logical comparison)
    effective_supply_slots = int(day_context['supply'] // WATER_REQ)

    # Determine competition level
    is_highly_competitive = effective_supply_slots < num_alive_opponents + 1
    is_moderately_competitive = effective_supply_slots < num_alive_opponents + 2

    # Base bid calculation based on my status and current competition
    target_bid_level = 0.0
    if my_status['hp'] <= 2: # Critical HP
        target_bid_level = DAILY_SALARY * 0.95
    elif my_status['no_water_days'] >= 1: # Missed water yesterday
        target_bid_level = DAILY_SALARY * 0.85
    elif is_highly_competitive: # Supply is very tight relative to demand
        target_bid_level = DAILY_SALARY * 0.75
    elif is_moderately_competitive: # Supply is somewhat tight
        target_bid_level = DAILY_SALARY * 0.65
    else: # Ample supply
        target_bid_level = DAILY_SALARY * 0.55

    # Adjust bid based on opponent's previous behavior
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None: # Check if 'bid' exists in previous_trace
            yesterday_bids.append(prev['bid'])

    final_bid = target_bid_level

    if not alive_opponents: # No opponents, bid minimum to secure water cheaply
        final_bid = DAILY_SALARY * 0.1
    elif yesterday_bids: # Adjust based on opponent bids from yesterday
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents were very aggressive
        if highest_prev_bid >= DAILY_SALARY * 0.8: # High threshold for aggression
            if my_status['hp'] > 3 and not is_highly_competitive: # Healthy and not super competitive day, try to save
                final_bid = min(target_bid_level, DAILY_SALARY * 0.5)
            else: # Need water or very competitive, outbid aggressively
                final_bid = max(target_bid_level, highest_prev_bid + 5)
        # If opponents were moderately aggressive
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # Moderate threshold
            final_bid = max(target_bid_level, highest_prev_bid + 2.5) # Slightly outbid them
        # If opponents were conservative
        else:
            final_bid = max(target_bid_level, average_prev_bid + 1) # Just a bit above average to win cheaply

    # Final adjustments: Ensure bid doesn't exceed budget and is positive
    final_bid = min(my_status['budget'], final_bid)
    final_bid = max(0.01, final_bid) # Bid at least 0.01 to participate and avoid zero bid issues

    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    HEALTHY_HP_THRESHOLD = 3 # HP > 3 is considered healthy

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents are alive, bid minimum to survive
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine bid based on yesterday's highest bid and my HP
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # High competition detected if highest previous bid is substantial
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Threshold for high competition: 120
            if my_status['hp'] > HEALTHY_HP_THRESHOLD: # Healthy, can afford to save a bit but still compete
                # Bid enough to stay in contention, but not necessarily win against max bidder
                return min(my_status['budget'], DAILY_SALARY * 0.65) # 97.5
            else: # Unhealthy (HP <= 3), must bid very high to secure water
                return min(my_status['budget'], DAILY_SALARY * 0.95) # 142.5
        else: # Moderate competition
            # Bid slightly above highest previous bid, ensuring a minimum to secure water
            return min(my_status['budget'], max(DAILY_SALARY * 0.6, highest_prev_bid + 5)) # 90 or highest_prev_bid + 5
    else: # No previous bids from alive opponents (e.g., first day or all opponents are new)
        if my_status['hp'] <= HEALTHY_HP_THRESHOLD: # Unhealthy, bid high to secure water
            return min(my_status['budget'], DAILY_SALARY * 0.9) # 135
        else: # Healthy, bid moderately to conserve budget
            return min(my_status['budget'], DAILY_SALARY * 0.7) # 105
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

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid_amount = DAILY_SALARY * 0.6 # Default competitive bid (90)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If opponents were bidding very high (e.g., > 85% of salary)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 4: # My HP is good, still compete but manage budget
                bid_amount = max(bid_amount, highest_prev_bid + 1.0)
                bid_amount = min(bid_amount, DAILY_SALARY * 0.9) # Cap at 90% of salary
            else: # My HP is critical, I MUST get water
                bid_amount = DAILY_SALARY * 0.98 # Very aggressive
        else: # Opponents were bidding moderately or low
            # Try to win by bidding slightly above them, but don't overpay too much
            bid_amount = max(bid_amount, highest_prev_bid + 5.0)
            bid_amount = min(bid_amount, DAILY_SALARY * 0.88) # Cap at 88% of salary

    # Adjust for end-game desperation (last 2 days)
    if day_context['day'] >= EPISODE_DAYS - 1:
        if my_status['hp'] <= 5: # If HP is low, become more desperate
            bid_amount = max(bid_amount, DAILY_SALARY * 0.9)
        else: # If HP is good, maintain competitive bid, but slightly higher
            bid_amount = max(bid_amount, DAILY_SALARY * 0.8)

    # Critical HP override: if HP is very low, bid extremely aggressively
    if my_status['hp'] <= 3:
        bid_amount = DAILY_SALARY * 0.99

    # Ensure bid is within budget and at least 1
    final_bid = max(1.0, min(bid_amount, my_status['budget']))

    return final_bid
"""
