# ============================================================
# Experiment: exp_028
# Agent: Cindy
# Source: exp_028
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Scenario 1: No active opponents - bid minimally
    if not alive_opponents:
        return min(my_status['budget'], 1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Scenario 2: Critical desperation - death imminent
    if my_status['no_water_days'] == 2:
        # Must get water at almost any cost
        return min(my_status['budget'], DAILY_SALARY * 0.99)

    # Scenario 3: High pressure from opponents based on yesterday's bids
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if my_status['hp'] > 3 and my_status['no_water_days'] == 0:
            # I'm healthy and got water yesterday, can afford to let others overbid and save budget.
            return min(my_status['budget'], DAILY_SALARY * 0.3)
        else:
            # My HP is not great or I missed water, I need to compete aggressively.
            return min(my_status['budget'], DAILY_SALARY * 0.95)

    # Scenario 4: Missed water once (no_water_days == 1) - need water but not critical yet
    if my_status['no_water_days'] == 1:
        # Bid high to ensure getting water, but leave some budget if possible.
        return min(my_status['budget'], DAILY_SALARY * 0.75)

    # Scenario 5: Low HP (general health) - prioritize getting water if health is low.
    if my_status['hp'] <= 2:
        # Overall health is low, prioritize getting water.
        return min(my_status['budget'], DAILY_SALARY * 0.8)

    # Scenario 6: General bidding strategy - no immediate threats, moderate bidding.
    if highest_prev_bid > 0:
        # Try to slightly outbid the highest moderate bid from yesterday to secure water.
        return min(my_status['budget'], max(DAILY_SALARY * 0.55, highest_prev_bid + 1.5))
    
    # Default moderate bid if no previous bids or specific conditions met.
    return min(my_status['budget'], DAILY_SALARY * 0.55)
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
    
    # If I'm the only one left, bid minimally to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Base bid: a solid amount to show presence
    bid_value = DAILY_SALARY * 0.6

    # Look for Alex's previous bid specifically
    alex_yesterday_bid = 0
    for agent_id, opp_data in opponents_status.items():
        if opp_data['alive'] and agent_id == 'Alex':
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                alex_yesterday_bid = prev['bid']
            break

    # If Alex bid high yesterday, I need to counter aggressively
    if alex_yesterday_bid > DAILY_SALARY * 0.9: # Alex is very aggressive
        bid_value = max(bid_value, alex_yesterday_bid + 1.0) # Bid slightly above Alex's high bid
    elif alex_yesterday_bid > 0: # Alex bid, but not extremely high
        bid_value = max(bid_value, alex_yesterday_bid * 1.05) # Incrementally higher than Alex

    # Adjust bid based on my HP
    # If HP is critical, bid even higher
    if my_status['hp'] <= 2: # Very low HP
        bid_value = max(bid_value, DAILY_SALARY * 1.1) # Bid above salary if needed and budget allows
    elif my_status['hp'] <= 5: # Low HP
        bid_value = max(bid_value, DAILY_SALARY * 0.9) # Bid very high, close to salary

    # Consider days remaining - if near the end and low HP, be even more aggressive
    days_left = EPISODE_DAYS - day_context['day']
    if days_left <= 2 and my_status['hp'] <= 3:
        bid_value = max(bid_value, DAILY_SALARY * 1.2) # Maximize chances to survive last days

    # Ensure bid doesn't exceed current budget
    final_bid = min(my_status['budget'], bid_value)
    
    # Ensure a minimal bid if budget is available and final_bid is somehow 0
    if final_bid == 0 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.05)
    
    # Ensure bid is always positive if budget allows, to participate
    if final_bid <= 0 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], 1.0) # Bid at least 1.0

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

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    total_water_needed_for_all = WATER_REQ
    for opp in alive_opponents:
        total_water_needed_for_all += opp['water_requirement']

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.55

    if day_context['supply'] < total_water_needed_for_all:
        base_bid = max(base_bid, DAILY_SALARY * 0.7)
        if day_context['supply'] < (total_water_needed_for_all * 0.8):
            base_bid = max(base_bid, DAILY_SALARY * 0.85)
    elif day_context['supply'] > total_water_needed_for_all * 1.5:
        base_bid = min(base_bid, DAILY_SALARY * 0.4)

    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        base_bid = max(base_bid, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4 and day_context['day'] > EPISODE_DAYS / 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.7:
            base_bid = max(base_bid, highest_prev_bid + (DAILY_SALARY * 0.03))
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            base_bid = max(base_bid, highest_prev_bid + (DAILY_SALARY * 0.01))

        if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
             base_bid = max(base_bid, highest_prev_bid + 1.0)

    final_bid = min(my_status['budget'], base_bid)

    if final_bid <= 0 and my_status['budget'] > 0:
        return 0.01

    return final_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta_round_state

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no active opponents, bid conservatively
    if not alive_opponents:
        # Enough water for me, no competition. Bid low to save budget.
        return min(my_budget, DAILY_SALARY * 0.1)

    # Analyze opponent's previous bids from the current meta-round's 'previous_trace'
    highest_prev_bid = 0.0
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev_trace['bid'])

    # Determine base bid
    base_bid = DAILY_SALARY * 0.5 # Default to 50% of salary

    # Adjust bid based on my HP
    if my_hp <= 2: # Critical HP, need water desperately
        base_bid = DAILY_SALARY * 0.9 # Bid 90% of salary
    elif my_hp <= 5: # Low HP, need water to recover
        base_bid = DAILY_SALARY * 0.75 # Bid 75% of salary

    # Adjust bid based on previous opponent bids
    if highest_prev_bid > 0:
        # If opponent bid high, I need to bid higher to secure water
        # Add a small margin to ensure winning, but not excessively
        base_bid = max(base_bid, highest_prev_bid + 5.0)

    # Consider the number of days left.
    days_left = EPISODE_DAYS - current_day
    if days_left <= 2 and my_hp > 0: # Near end of game, if I'm still alive
        # Be more aggressive to secure survival and win
        base_bid = max(base_bid, DAILY_SALARY * 0.8) # Bid at least 80% of salary

    # Ensure bid does not exceed available budget
    final_bid = min(my_budget, base_bid)

    # Ensure bid is not negative or ridiculously low if budget allows more
    if final_bid < 1.0 and my_budget >= 1.0:
        final_bid = 1.0 # Minimum bid to participate

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
    
    # If no opponents, bid minimally to secure water
    if not alive_opponents:
        return min(my_status['budget'], 1.0) if my_status['budget'] > 0 else 0.0

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Strategy based on opponent's previous bids and my health
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were very aggressive yesterday (e.g., bidding >= 85% of daily salary)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # If healthy, conserve budget and let others fight for high bids
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            else: # If HP is low, bid aggressively to survive
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else: # Opponents were not extremely aggressive, bid competitively
            # Bid at least 50% of salary, or slightly more than highest previous bid
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))

    # If no yesterday bids (e.g., first day or opponents were not active/died)
    # Or if yesterday_bids list is empty (no trace for alive opponents)
    if my_status['hp'] <= 2: # Critical HP, bid high to survive
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    
    # Default bid for healthy state or early days with no strong signals
    return min(my_status['budget'], DAILY_SALARY * 0.55)
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
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    potential_water_slots = int(current_supply / WATER_REQ)

    bid_strategy = DAILY_SALARY * 0.55

    if my_hp <= 2:
        bid_strategy = DAILY_SALARY * 0.95
    elif my_hp <= 5:
        bid_strategy = DAILY_SALARY * 0.75
    elif my_hp >= 8 and current_day < EPISODE_DAYS * 0.7:
        bid_strategy = DAILY_SALARY * 0.4

    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_hp <= 5:
                bid_strategy = max(bid_strategy, highest_prev_bid + 5)
            elif potential_water_slots > num_alive_opponents:
                bid_strategy = max(bid_strategy, highest_prev_bid * 0.8)
            else:
                bid_strategy = max(bid_strategy, highest_prev_bid + 1.5)
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            if my_hp <= 5:
                bid_strategy = max(bid_strategy, highest_prev_bid + 3)
            else:
                bid_strategy = max(bid_strategy, highest_prev_bid + 1)
        else:
            bid_strategy = max(bid_strategy, highest_prev_bid + 1)

    if potential_water_slots <= num_alive_opponents:
        if my_hp <= 5:
            bid_strategy = max(bid_strategy, DAILY_SALARY * 0.8)
        else:
            bid_strategy = max(bid_strategy, DAILY_SALARY * 0.65)
    elif potential_water_slots > num_alive_opponents + 1:
        if bid_strategy > DAILY_SALARY * 0.6:
            pass
        else:
            bid_strategy = min(bid_strategy, DAILY_SALARY * 0.45)

    final_bid = min(my_budget, bid_strategy)
    final_bid = max(0.0, final_bid)

    if final_bid == 0 and my_budget > 0 and my_hp > 0:
        final_bid = 1.0

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
        return min(my_status['budget'], 1.0) 

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    bid = DAILY_SALARY * 0.7 

    if my_status['hp'] <= 2:
        bid = DAILY_SALARY * 0.95 
    elif my_status['hp'] <= 5:
        bid = DAILY_SALARY * 0.85 
    else:
        if highest_prev_bid > DAILY_SALARY * 0.6:
            bid = min(DAILY_SALARY * 0.8, highest_prev_bid + 5.0) 
        else:
            bid = DAILY_SALARY * 0.7 

    days_remaining = EPISODE_DAYS - day_context['day']
    if days_remaining <= 3 and my_status['budget'] > bid:
        bid = max(bid, DAILY_SALARY * 0.8)

    final_bid = min(bid, my_status['budget'])
    
    return max(1.0, final_bid)
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Determine a base bid - start strong as only one agent can get water
    bid_value = DAILY_SALARY * 0.75 # Default competitive bid (112.5)

    # Adjust bid based on my health and no-water-days (survival priority)
    if my_no_water_days == 2: # Critical: will die tomorrow without water
        bid_value = DAILY_SALARY * 0.98 # Bid almost full salary
    elif my_hp <= 3: # Low HP, need water urgently
        bid_value = DAILY_SALARY * 0.90
    elif my_no_water_days == 1: # Missed water yesterday
        bid_value = DAILY_SALARY * 0.85
    elif my_hp <= 5: # Medium low HP
        bid_value = DAILY_SALARY * 0.80

    # Adjust bid based on the day (become more aggressive towards the end)
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        bid_value = max(bid_value, DAILY_SALARY * 0.95)
    elif current_day >= EPISODE_DAYS - 4: # Last 4 days
        bid_value = max(bid_value, DAILY_SALARY * 0.88)

    # React to opponents' previous bids from 'previous_trace'
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If my current bid is not enough to beat the highest previous bid, increase it
        if bid_value < highest_prev_bid + 1.0:
            if my_hp <= 5 or my_no_water_days >= 1: # If I really need water
                bid_value = highest_prev_bid + 2.0 # Try to outbid by a small margin
            else: # If my HP is good, still try to win but don't overspend too much
                bid_value = max(bid_value, highest_prev_bid + 1.0)
    else:
        # If no previous bids (e.g., Day 1 or all opponents are new/died)
        # Bid aggressively on Day 1 to set a strong precedent
        if current_day == 1:
            bid_value = max(bid_value, DAILY_SALARY * 0.85)
        else:
            bid_value = max(bid_value, DAILY_SALARY * 0.75) # Default strong bid

    # Ensure bid meets a minimum floor, but doesn't exceed budget
    min_effective_bid = min(DAILY_SALARY * 0.2, my_budget) if my_budget > 0 else 0.0
    bid_value = max(bid_value, min_effective_bid)

    # Final cap: bid cannot exceed available budget
    bid_value = min(bid_value, my_budget)

    # If budget is 0, bid 0
    if my_budget <= 0:
        bid_value = 0.0

    return round(bid_value, 2)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid a minimal amount to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Check if my HP is critically low
    if my_status['hp'] <= 2:
        # Bid very aggressively to ensure survival
        return min(my_status['budget'], DAILY_SALARY * 0.99)

    # Collect yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace')
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # Determine the base bid
    # Start with a competitive base bid
    calculated_bid = DAILY_SALARY * 0.75

    # Adjust bid based on yesterday's highest opponent bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were bidding high, increase my bid slightly above the highest
        calculated_bid = max(calculated_bid, highest_prev_bid + 1)
    
    # Consider the number of remaining days
    days_left = EPISODE_DAYS - day_context['day']
    if days_left <= 2 and my_status['hp'] <= 3:
        # Near end of game and HP is not great, bid more aggressively
        calculated_bid = max(calculated_bid, DAILY_SALARY * 0.9)

    # Cap the bid to prevent excessive spending, unless HP is critical (handled above)
    # This cap helps manage budget over the long term
    calculated_bid = min(calculated_bid, DAILY_SALARY * 1.1)

    # Ensure the bid does not exceed current budget
    return min(my_status['budget'], calculated_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    # Initialize base bid
    bid_amount = DAILY_SALARY * 0.6 # Base competitive bid (90)

    # 1. Adjust bid based on my HP
    if my_status['hp'] <= 3: # Critical HP
        bid_amount = DAILY_SALARY * 0.95 # 142.5
    elif my_status['hp'] <= 5: # Low HP
        bid_amount = DAILY_SALARY * 0.85 # 127.5

    # 2. Adjust bid based on remaining days (end game pressure)
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: # Last 2 days, bid aggressively
        bid_amount = max(bid_amount, DAILY_SALARY * 0.9) # 135

    # 3. Analyze strong opponents' previous bids (Alex and Eric)
    strong_opponent_prev_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive'] and (opp_id == 'Alex' or opp_id == 'Eric'):
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                strong_opponent_prev_bids.append(prev['bid'])
        # Also consider if weak opponents unexpectedly bid high
        elif opp['alive'] and opp_id in ['Bob', 'David']:
             prev = opp.get('previous_trace', {})
             if prev and prev.get('bid') is not None and prev['bid'] > DAILY_SALARY * 0.3: # If they showed some aggression
                 strong_opponent_prev_bids.append(prev['bid'])

    if strong_opponent_prev_bids:
        max_prev_bid = max(strong_opponent_prev_bids)
        # If strong opponents bid high, we need to compete or slightly outbid
        if max_prev_bid >= DAILY_SALARY * 0.8: # If they bid >= 120
            bid_amount = max(bid_amount, max_prev_bid + 5)
        elif max_prev_bid >= DAILY_SALARY * 0.6: # If they bid >= 90
            bid_amount = max(bid_amount, max_prev_bid + 2)
        else: # If their bids were moderate, ensure we still bid enough
            bid_amount = max(bid_amount, DAILY_SALARY * 0.5) # 75

    # 4. Budget management
    # Ensure bid does not exceed available budget
    bid_amount = min(bid_amount, my_status['budget'])

    # If budget is very high, be more aggressive to secure water and potentially eliminate others
    if my_status['budget'] > DAILY_SALARY * 5 and my_status['hp'] > 5: # Budget > 750 and healthy
        bid_amount = max(bid_amount, DAILY_SALARY * 0.9) # 135

    # If budget is low, conserve but still try to get water
    if my_status['budget'] < DAILY_SALARY * 1.5 and my_status['hp'] > 2: # Budget < 225, but not critical HP
        bid_amount = min(bid_amount, DAILY_SALARY * 0.75) # Cap bid at 112.5

    # Ensure a minimum bid if budget allows, to stay active
    if bid_amount < DAILY_SALARY * 0.1 and my_status['budget'] >= DAILY_SALARY * 0.1:
        bid_amount = DAILY_SALARY * 0.1

    # Final check to ensure bid is non-negative
    bid_amount = max(0.0, bid_amount)

    return bid_amount
"""
