# ============================================================
# Experiment: exp_015
# Agent: Cindy
# Source: exp_015
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    # MAX_SUPPLY = 25 # Not directly used in bidding logic
    # MIN_SUPPLY = 15 # Not directly used in bidding logic
    EPISODE_DAYS = 10 # From meta_round_state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Determine base bid based on my HP and the fact that only one unit of water is available
    # (supply_range 15-25, my_water_req 13 means supply // WATER_REQ is always 1)
    if my_status['hp'] <= 2: # Critical state, must get water
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] == 3: # Getting low, high priority
        base_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] == 4: # Moderate HP, aim for water but can be outbid
        base_bid = DAILY_SALARY * 0.6
    else: # my_status['hp'] == 5 (full HP) - can afford to be less aggressive
        base_bid = DAILY_SALARY * 0.45

    # Adjust bid based on day progression (later days, more desperate)
    current_day = day_context['day']
    if current_day > EPISODE_DAYS * 0.7 and my_status['hp'] <= 3: # Late game, low HP
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif current_day > EPISODE_DAYS * 0.5 and my_status['hp'] <= 4: # Mid-late game, moderate HP
        base_bid = max(base_bid, DAILY_SALARY * 0.7)

    # Consider opponent's previous bids
    highest_prev_opp_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_opp_bid = max(highest_prev_opp_bid, prev['bid'])

    final_bid = base_bid

    if num_alive_opponents > 0:
        if highest_prev_opp_bid > 0:
            # If opponents were bidding high, I might need to bid higher to secure water.
            if my_status['hp'] <= 4: # If not full HP, I should try to win by outbidding
                final_bid = max(final_bid, highest_prev_opp_bid + 1)
            else: # Full HP, can risk letting others win if bid is too high
                # Still try to win if it's not much more than my base and below a threshold
                if highest_prev_opp_bid + 1 < DAILY_SALARY * 0.65: # A slightly higher threshold than base_bid
                    final_bid = max(final_bid, highest_prev_opp_bid + 1)
                # else, stick to my base_bid (DAILY_SALARY * 0.45) or let it be if too high
        else:
            # No previous bids or all were 0, assume moderate competition
            # My base_bid should be fine, slightly higher if many opponents and I need water
            if num_alive_opponents >= 2 and my_status['hp'] <= 4:
                final_bid = max(final_bid, DAILY_SALARY * 0.6) # Slightly more aggressive

    # Ensure bid does not exceed budget
    final_bid = min(final_bid, my_status['budget'])

    # Ensure bid is at least 1 if I need water and can afford it
    if final_bid < 1 and my_status['budget'] >= 1:
        final_bid = 1
    elif final_bid < 0: # Should not happen with min(final_bid, budget) but as a safeguard
        final_bid = 0

    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQUIREMENT = 13
    MY_DAILY_SALARY = 150
    EPISODE_DAYS = 10
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    max_total_value = MY_DAILY_SALARY

    bid = max_total_value * 0.5

    day_progress_ratio = current_day / EPISODE_DAYS
    bid += day_progress_ratio * (max_total_value * 0.2)

    if my_hp <= 2:
        bid = max_total_value * 0.95
    elif my_hp <= 4:
        bid = max_total_value * 0.8
    elif my_no_water_days >= 1:
        bid += max_total_value * 0.1

    supply_scarcity_factor = 0
    supply_range = MAX_SUPPLY - MIN_SUPPLY
    if supply_range > 0:
        supply_scarcity_factor = (MAX_SUPPLY - current_supply) / supply_range
    bid += supply_scarcity_factor * (max_total_value * 0.2)

    max_opponent_winning_bid_yesterday = 0.0
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('status') == 'water_allocated':
            max_opponent_winning_bid_yesterday = max(max_opponent_winning_bid_yesterday, prev['bid'])

    if max_opponent_winning_bid_yesterday > 0:
        if bid < max_opponent_winning_bid_yesterday + (max_total_value * 0.02):
            bid = max_opponent_winning_bid_yesterday + (max_total_value * 0.02)

    bid = min(bid, my_budget)
    bid = max(bid, max_total_value * 0.1)

    if my_hp <= 1 and my_budget > 0:
        bid = my_budget

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

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    bid = DAILY_SALARY * 0.6

    if my_status['hp'] <= 2:
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5:
        bid = DAILY_SALARY * 0.85
    else:
        if day_context['supply'] / WATER_REQ >= 2:
            bid = DAILY_SALARY * 0.55
        else:
            bid = DAILY_SALARY * 0.7

    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 5:
                bid = max(bid, highest_prev_bid + 2)
            else:
                bid = max(bid, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            bid = max(bid, highest_prev_bid + 1)

    final_bid = min(my_status['budget'], bid)
    final_bid = max(final_bid, DAILY_SALARY * 0.1)

    return final_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # Total days in a meta-round

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # 1. Emergency Bidding (Survival Priority)
    if my_hp <= 2: # Critical health, must get water
        bid = DAILY_SALARY * 0.99
    elif my_no_water_days >= 1: # Missed water yesterday, need to win today
        bid = DAILY_SALARY * 0.95
    elif current_day >= EPISODE_DAYS - 2: # Last few days, ensure survival to finish
        bid = DAILY_SALARY * 0.90
    elif not alive_opponents: # No competition, bid minimum to save budget
        bid = DAILY_SALARY * 0.1
    else:
        # 2. Normal Competition Bidding
        yesterday_bids = []
        for opp in alive_opponents:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            # Base bid is slightly higher than highest opponent bid from yesterday
            # Adjust increment based on my HP
            if my_hp > 7: # Good health, can be slightly less aggressive
                bid = highest_prev_bid + 3
            elif my_hp > 4: # Moderate health
                bid = highest_prev_bid + 7
            else: # Lower health, be more aggressive
                bid = highest_prev_bid + 12
            
            # Ensure bid is at least a reasonable floor, even if opponents bid very low
            bid = max(bid, DAILY_SALARY * 0.65) 
        else:
            # No previous bids from any alive opponent, assume moderate competition
            bid = DAILY_SALARY * 0.7

    # Final adjustments and caps
    final_bid = min(my_budget, bid)
    final_bid = min(final_bid, DAILY_SALARY) # Cap bid at daily salary
    final_bid = max(1, final_bid) # Bid must be at least 1

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

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to get water
    if not alive_opponents:
        return min(my_current_budget, DAILY_SALARY * 0.1)

    # Calculate total water demand including myself
    total_water_demand = WATER_REQ
    for opp in alive_opponents:
        total_water_demand += opp['water_requirement']

    # --- Base Bid Strategy ---
    # Default bid, adjusted by HP
    if my_current_hp <= 2: # Critical HP: bid very high
        bid_amount = DAILY_SALARY * 0.95
    elif my_current_hp <= 4: # Low HP: bid high
        bid_amount = DAILY_SALARY * 0.85
    elif current_day > EPISODE_DAYS * 0.7: # Late game, ensure survival
        bid_amount = DAILY_SALARY * 0.75
    else: # Healthy or early/mid game: moderate bid
        bid_amount = DAILY_SALARY * 0.6

    # --- React to Opponent's previous_trace ---
    yesterday_bids = []
    desperate_opponents = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
        if opp['no_water_days'] > 0 or opp['hp'] <= 3:
            desperate_opponents += 1

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If opponents bid very high yesterday, we need to be competitive
        if highest_prev_bid >= DAILY_SALARY * 0.9: # e.g., >= 135
            if my_current_hp > 3: # Not critical, but still need to compete
                bid_amount = max(bid_amount, highest_prev_bid * 1.01) # Slightly outbid
            else: # Critical HP, must win
                bid_amount = max(bid_amount, highest_prev_bid * 1.05)
        # If opponents bid moderately high
        elif highest_prev_bid >= DAILY_SALARY * 0.7: # e.g., >= 105
            bid_amount = max(bid_amount, highest_prev_bid * 1.01)
        # If opponents bid low and I'm healthy, try to save
        elif highest_prev_bid < DAILY_SALARY * 0.5 and my_current_hp > 5: # e.g., < 75
            bid_amount = min(bid_amount, highest_prev_bid * 1.1)

    # --- Adjust for Scarcity and Desperation ---
    # If supply is tight compared to demand
    if current_supply < total_water_demand:
        # If there are more agents than water slots
        num_slots = int(current_supply // WATER_REQ) # Use int() for safety, though not an index here.
        if num_slots < len(alive_opponents) + 1:
            # Increase bid if water is scarce and many opponents are desperate
            if desperate_opponents > 0 and my_current_hp <= 4:
                bid_amount = max(bid_amount, DAILY_SALARY * 1.0) # Bid up to salary to survive
            elif desperate_opponents > 0:
                bid_amount = max(bid_amount, DAILY_SALARY * 0.8) # Increase bid if others are desperate

    # --- Final Bid Constraints ---
    final_bid = min(my_current_budget, bid_amount)

    # Ensure bid is never zero or negative if budget allows
    if final_bid <= 0 and my_current_budget > 0:
        return min(my_current_budget, 1.0)
    elif final_bid <= 0:
        return 0.0
    
    # Cap bid to prevent overspending significantly beyond daily salary, unless extremely critical
    if my_current_hp <= 1: # Extreme desperation
        final_bid = min(final_bid, my_current_budget) # No upper cap if extremely critical and budget allows
    else:
        final_bid = min(final_bid, DAILY_SALARY * 1.2) # Cap at 120% of salary

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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to save budget but still get water
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Base bid: Start with a strong bid
    target_bid = DAILY_SALARY * 0.70

    # Analyze yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Aim to slightly outbid the highest opponent bid from yesterday
        target_bid = max(target_bid, highest_prev_bid + 2.0)

    # Aggressive bidding if HP is low or I haven't received water
    if my_hp <= 3: # Critical HP
        target_bid = max(target_bid, DAILY_SALARY * 0.98)
    elif my_no_water_days >= 1: # Missed water yesterday
        target_bid = max(target_bid, DAILY_SALARY * 0.9)
    elif my_hp <= 5: # Low HP
        target_bid = max(target_bid, DAILY_SALARY * 0.85)

    # Late game aggression
    # If it's the last day and I need water, bid all I have
    if current_day == EPISODE_DAYS and my_no_water_days < 2:
        target_bid = my_budget
    elif current_day >= EPISODE_DAYS - 1: # Last two days, be very aggressive
        target_bid = max(target_bid, DAILY_SALARY * 0.99)
        if my_hp <= 5:
            target_bid = max(target_bid, my_budget * 0.9)

    # Ensure bid does not exceed budget
    final_bid = min(my_budget, target_bid)

    # Ensure bid is not negative
    final_bid = max(0.0, final_bid)

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
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_previous_bid = 0
    if yesterday_bids:
        max_previous_bid = max(yesterday_bids)

    bid_amount = 0.0

    if my_status['hp'] <= WATER_REQ: # Critically low HP, must win
        target_bid = DAILY_SALARY * 1.05 # Bid slightly above salary
        if max_previous_bid > 0:
            target_bid = max(target_bid, max_previous_bid + 5) # Ensure outbid previous high
        bid_amount = min(my_status['budget'], target_bid)

    elif my_status['hp'] <= WATER_REQ * 2: # Very low HP, strong need to win
        target_bid = DAILY_SALARY * 0.98
        if max_previous_bid > 0:
            target_bid = max(target_bid, max_previous_bid + 3)
        bid_amount = min(my_status['budget'], target_bid)

    elif my_status['hp'] <= WATER_REQ * 3: # Low HP, moderate need to win
        target_bid = DAILY_SALARY * 0.90
        if max_previous_bid > 0:
            target_bid = max(target_bid, max_previous_bid + 2)
        bid_amount = min(my_status['budget'], target_bid)

    else: # Good HP, can afford to be more flexible
        if max_previous_bid >= DAILY_SALARY * 0.95: # Opponents bidding very high
            # If my HP is good, consider letting them win to drain their budget.
            target_bid = DAILY_SALARY * 0.75 # Conserve budget
        else: # Opponents not bidding excessively high, try to win
            target_bid = DAILY_SALARY * 0.85
            if max_previous_bid > 0:
                target_bid = max(target_bid, max_previous_bid + 1) # Slightly outbid
        bid_amount = min(my_status['budget'], target_bid)

    final_bid = max(0.0, bid_amount)

    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    # Calculate remaining days
    remaining_days = EPISODE_DAYS - day_context['day']

    # Identify alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid very low to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from all alive opponents
    yesterday_bids = []
    strong_opponents_yesterday_bids = [] # To specifically track Bob and Eric
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
                if opp_id in ["Bob", "Eric"]:
                    strong_opponents_yesterday_bids.append(prev['bid'])

    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0
    max_strong_opp_yesterday_bid = max(strong_opponents_yesterday_bids) if strong_opponents_yesterday_bids else 0

    # Base bid strategy
    base_bid = DAILY_SALARY * 0.6 # A competitive but not overly aggressive starting point

    # Adjust bid based on my HP and urgency
    if my_status['hp'] <= 2: # Critical HP, bid very aggressively
        bid = min(my_status['budget'], DAILY_SALARY * 1.5)
    elif my_status['hp'] <= 4: # Low HP, bid aggressively
        # Try to beat strong opponents if they were active, otherwise a high base
        bid = min(my_status['budget'], max(max_strong_opp_yesterday_bid + 10, DAILY_SALARY * 0.9))
    elif my_status['no_water_days'] > 0: # Missed water yesterday, need to get it today
        # Try to beat strong opponents if they were active, otherwise a solid bid
        bid = min(my_status['budget'], max(max_strong_opp_yesterday_bid + 5, DAILY_SALARY * 0.8))
    else: # Healthy HP
        # Consider supply and opponent behavior
        # Supply is generally tight (15-25 for WATER_REQ=13 means < 2 full requirements)
        if max_strong_opp_yesterday_bid > 0: # Strong opponents are active and bid high yesterday
            bid = max(max_strong_opp_yesterday_bid + 1, base_bid) # Slightly beat the strong ones
        elif max_yesterday_bid > 0: # Other opponents (Alex, David) were active and bid yesterday
            bid = max(max_yesterday_bid * 0.9, DAILY_SALARY * 0.4) # Bid a bit below their max, but at least a moderate amount
        else: # No strong bids yesterday, or only weak ones, or early game
            bid = DAILY_SALARY * 0.3 # Conserve more

    # Final budget check
    bid = min(bid, my_status['budget'])

    # If it's the last day and I have high budget, I can afford to spend more to secure water/win
    if remaining_days <= 1 and my_status['budget'] > DAILY_SALARY * 2:
        bid = min(my_status['budget'], bid * 1.2)

    # Ensure bid is at least 1, unless budget is 0
    if bid <= 0 and my_status['budget'] > 0:
        bid = 1.0
    elif my_status['budget'] == 0:
        bid = 0.0

    return float(bid)
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
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    total_water_needed = WATER_REQ
    for opp in alive_opponents:
        total_water_needed += opp['water_requirement']

    base_bid = DAILY_SALARY * 0.5

    if current_supply < total_water_needed * 0.8:
        base_bid *= 1.4
    elif current_supply < total_water_needed * 1.2:
        base_bid *= 1.15
    else:
        base_bid *= 0.8

    if my_hp <= 2:
        base_bid = DAILY_SALARY * 1.05
    elif my_hp <= 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif my_hp >= 8:
        base_bid *= 0.85

    day_aggression_factor = 1 + (current_day / EPISODE_DAYS) * 0.2
    base_bid *= day_aggression_factor

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)

        if max_yesterday_bid >= DAILY_SALARY * 0.8:
            if my_hp <= 4:
                base_bid = max(base_bid, max_yesterday_bid * 1.05)
            else:
                base_bid = max(base_bid, max_yesterday_bid * 1.01)
        elif max_yesterday_bid <= DAILY_SALARY * 0.3:
            base_bid = min(base_bid, max_yesterday_bid * 0.9)
        else:
            base_bid = max(base_bid, avg_yesterday_bid * 1.02)

    final_bid = max(1.0, min(base_bid, my_budget))

    if my_hp <= 1:
        final_bid = min(my_budget, max(final_bid, DAILY_SALARY * 1.1))
    elif my_hp <= 3:
        final_bid = min(my_budget, max(final_bid, DAILY_SALARY * 0.95))

    return round(final_bid, 2)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid a minimal amount to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine bidding strategy based on my HP and opponent's previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If highest previous bid was very high, react strategically
        if highest_prev_bid >= DAILY_SALARY * 0.85: # Threshold for high opponent bid (127.5)
            if my_status['hp'] > 3: # If I'm relatively healthy, take a risk and save budget
                return min(my_status['budget'], DAILY_SALARY * 0.3) # Bid low (45) to let opponents fight
            else: # If my HP is critical (<= 3), bid very aggressively to survive
                return min(my_status['budget'], DAILY_SALARY * 0.95) # Bid very high (142.5)

        else: # If highest previous bid was moderate or low (< 127.5)
            if my_status['hp'] <= 2: # If my HP is critical
                return min(my_status['budget'], DAILY_SALARY * 0.9) # Bid high (135)
            else: # If my HP is healthy or moderately healthy, bid slightly above previous high
                # Ensure it's at least a base competitive bid (82.5)
                return min(my_status['budget'], max(DAILY_SALARY * 0.55, highest_prev_bid + 1.5))

    else: # No previous bids from alive opponents (e.g., Day 1)
        if my_status['hp'] <= 2: # If my HP is critical
            return min(my_status['budget'], DAILY_SALARY * 0.9) # Bid high (135)
        else: # If my HP is healthy
            return min(my_status['budget'], DAILY_SALARY * 0.55) # Bid moderately (82.5)
"""
