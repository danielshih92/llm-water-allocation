# ============================================================
# Experiment: exp_097
# Agent: Cindy
# Source: exp_097
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimum to get water
    if num_alive_opponents == 0:
        return min(my_status['budget'], 1) # Bid 1 to secure water with no competition

    # Calculate total water requirement from all agents
    total_water_needed = WATER_REQ + sum(opp['water_requirement'] for opp in alive_opponents)

    supply = day_context['supply']
    
    # Base bid percentage based on HP
    base_bid_percentage = 0.5 # Default starting point
    if my_status['hp'] <= 2: # Critical HP
        base_bid_percentage = 0.95
    elif my_status['hp'] <= 4: # Low HP
        base_bid_percentage = 0.75
    elif my_status['hp'] <= 6: # Medium HP
        base_bid_percentage = 0.6
    else: # Healthy HP
        base_bid_percentage = 0.45

    # Adjust bid based on supply scarcity and number of opponents
    # If supply is less than total potential demand, increase bid
    if supply < total_water_needed:
        base_bid_percentage += 0.1 
    # If supply is abundant compared to demand and few opponents, decrease bid slightly
    elif supply >= total_water_needed and num_alive_opponents < 2:
        base_bid_percentage -= 0.05

    # Cap bid percentage to stay within reasonable bounds (0.1 to 1.0 of daily salary)
    base_bid_percentage = max(0.1, min(1.0, base_bid_percentage))

    # Calculate the bid
    bid = DAILY_SALARY * base_bid_percentage

    # Ensure bid does not exceed current budget
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
    num_alive_opponents = len(alive_opponents)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Since supply (15-25) always yields only one water unit (WATER_REQ=13),
    # it's always high competition. Bids must be aggressive.
    base_bid = DAILY_SALARY * 0.8 # Start with 120, competitive with Alex/Eric's average bids.

    # Adjust bid to outcompete previous high bids
    bid = base_bid
    if highest_prev_bid > 0:
        # Try to slightly outbid the highest previous bid from strong opponents
        bid = max(bid, highest_prev_bid + 5)

    # HP-based adjustments: If HP is low, bid very aggressively
    if my_status['hp'] <= 3: # Very low HP, desperate for water
        bid = max(bid, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 5: # Low HP
        bid = max(bid, DAILY_SALARY * 0.90)

    # Budget constraints: Cannot bid more than current budget
    bid = min(bid, my_status['budget'])

    # If no opponents are alive, bid minimum to win
    if num_alive_opponents == 0:
        bid = min(my_status['budget'], 1.0)

    # Ensure bid is at least 1.0, unless budget is 0
    bid = max(1.0, bid) if my_status['budget'] > 0 else 0.0

    return float(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid minimally to save budget.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine the highest bid from yesterday among active opponents
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else DAILY_SALARY * 0.5 # Default if no bids found

    # Base bid calculation - start with a moderate percentage of daily salary
    # Adjust based on the current day to be more aggressive later
    base_bid = DAILY_SALARY * (0.6 + (day_context['day'] / EPISODE_DAYS) * 0.2) # Increases from 0.6 to 0.8 * DAILY_SALARY

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical survival mode
        bid_value = DAILY_SALARY * 0.95 # Very aggressive
    elif my_status['hp'] <= 4: # Low HP, need water
        bid_value = DAILY_SALARY * 0.85 # Aggressive
    else: # Healthy HP, can be more strategic
        bid_value = base_bid

    # Adjust bid based on supply scarcity/abundance
    # If supply is low, competition is higher
    # Supply range is [15, 25]. My requirement is 13.
    # If supply is close to my requirement, it's very competitive.
    if day_context['supply'] <= WATER_REQ + 3: # e.g., supply 15, 16
        bid_value *= 1.15 # Increase bid
    elif day_context['supply'] >= 22: # Abundant supply
        bid_value *= 0.9 # Decrease bid

    # React to highest opponent bid from yesterday
    # If my current calculated bid is less than what opponents bid, I might need to increase it
    # But only if I'm not in critical HP (where I'm already bidding max)
    if my_status['hp'] > 2 and bid_value < highest_prev_bid * 1.05: # Try to slightly outbid the highest if not critical
        bid_value = highest_prev_bid * 1.05
    
    # Ensure bid does not exceed my current budget
    final_bid = min(my_status['budget'], bid_value)
    
    # Ensure a minimum bid to stay in the game, but not excessively low
    final_bid = max(final_bid, DAILY_SALARY * 0.1) # Minimum bid to stay relevant

    # Cap the bid at a reasonable maximum, e.g., 1.2 times daily salary, to prevent overspending on a single day
    final_bid = min(final_bid, DAILY_SALARY * 1.2) # Max bid (180)

    return final_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid a minimal amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Calculate supply pressure factor based on current day's supply
    supply = day_context['supply']
    supply_pressure_factor = 1.0
    if supply <= 18.0: # Very tight supply
        supply_pressure_factor = 1.25
    elif supply <= 21.0: # Moderate tight supply
        supply_pressure_factor = 1.1
    else: # Ample supply
        supply_pressure_factor = 1.0

    # Base bid strategy adjusted for HP, no_water_days, and supply pressure
    bid = 0.0
    if my_status['no_water_days'] > 0: # Critical state, must get water
        # Bid very aggressively, try to outbid highest previous bid significantly
        bid = max(highest_prev_bid + 15, DAILY_SALARY * 0.95 * supply_pressure_factor)
        bid = min(bid, my_status['budget'], DAILY_SALARY * 1.3) # Cap at 1.3x salary if desperate
    elif my_status['hp'] <= 2: # Low HP, but not critical for missing water yet. Be aggressive but aim for profit.
        # Try to outbid previous high, but don't overspend too much
        bid = max(highest_prev_bid + 7, DAILY_SALARY * 0.75 * supply_pressure_factor)
        bid = min(bid, my_status['budget'], DAILY_SALARY * 1.1) # Cap slightly above salary
    else: # Healthy HP, aim for profit and conservative bidding
        # Try to slightly outbid previous high, but prioritize profit
        bid = max(highest_prev_bid + 2, DAILY_SALARY * 0.55 * supply_pressure_factor)
        bid = min(bid, my_status['budget'], DAILY_SALARY * 0.95) # Keep bid below salary for profit

    # Ensure bid is at least a minimal amount to participate
    bid = max(bid, DAILY_SALARY * 0.1)

    return float(bid)
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

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    average_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Given WATER_REQ = 13 and supply_range [15, 25], only one player can get their full requirement.
    # This means competition is always high for that single water slot.

    base_bid = DAILY_SALARY * 0.5 # Starting point for a competitive bid

    # Adjust bid based on my desperation
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        # Highly desperate, must win the water. Bid very aggressively.
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        # Moderately desperate.
        base_bid = DAILY_SALARY * 0.8
    else:
        # Not desperate, but still need to compete for the single slot.
        base_bid = DAILY_SALARY * 0.6

    # Factor in opponent's previous bids to stay competitive
    if highest_prev_bid > 0:
        # If opponents bid high yesterday, we need to at least match or slightly exceed.
        base_bid = max(base_bid, highest_prev_bid + 1)
    else:
        # If no previous bids or they were 0, use average or a slightly higher base.
        base_bid = max(base_bid, average_prev_bid + 1 if average_prev_bid > 0 else DAILY_SALARY * 0.5)

    # Consider the day progression: become more aggressive towards the end of the episode
    if current_day >= EPISODE_DAYS - 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.98)

    # Ensure bid doesn't exceed budget and is non-negative
    final_bid = min(my_status['budget'], base_bid)
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
    strong_opponent_ids = ["Bob", "David"]

    highest_strong_opp_bid = 0.0
    for opp_id, opp in opponents_status.items():
        if opp['alive'] and opp_id in strong_opponent_ids:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                if prev['bid'] > highest_strong_opp_bid:
                    highest_strong_opp_bid = prev['bid']
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

    overall_highest_prev_bid = 0.0
    if yesterday_bids:
        overall_highest_prev_bid = max(yesterday_bids)

    bid_amount = 0.0

    # Desperate state: Very low HP, need water immediately
    if my_status['hp'] <= 3:
        bid_amount = DAILY_SALARY * 1.5
        if overall_highest_prev_bid > 0:
            bid_amount = max(bid_amount, overall_highest_prev_bid + 20)
    
    # Critical state: Low to moderate HP, need to be competitive
    elif my_status['hp'] <= 6:
        bid_amount = DAILY_SALARY * 1.2
        if overall_highest_prev_bid > 0:
            bid_amount = max(bid_amount, overall_highest_prev_bid + 10)
    
    # Stable state: Good HP, but still need to win given tight supply
    else:
        if highest_strong_opp_bid > 0:
            if highest_strong_opp_bid >= DAILY_SALARY * 0.9:
                bid_amount = highest_strong_opp_bid + 5
            else:
                bid_amount = DAILY_SALARY * 1.0
        elif overall_highest_prev_bid > 0:
            if overall_highest_prev_bid >= DAILY_SALARY * 0.8:
                bid_amount = overall_highest_prev_bid + 2
            else:
                bid_amount = DAILY_SALARY * 0.9
        else:
            bid_amount = DAILY_SALARY * 0.95

    bid_amount = max(bid_amount, DAILY_SALARY * 0.1)

    return min(my_status['budget'], bid_amount)
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

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    base_bid = 0.0
    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.85
    elif my_status['hp'] <= 7:
        base_bid = DAILY_SALARY * 0.7
    else:
        base_bid = DAILY_SALARY * 0.6

    calculated_bid = base_bid
    if highest_prev_bid > 0.0:
        if my_status['hp'] <= 2:
            calculated_bid = max(base_bid, highest_prev_bid + 5.0)
        elif my_status['hp'] <= 4:
            calculated_bid = max(base_bid, highest_prev_bid + 3.0)
        elif my_status['hp'] <= 7:
            calculated_bid = max(base_bid, highest_prev_bid + 1.5)
        else:
            calculated_bid = max(base_bid, highest_prev_bid + 0.5)

    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2:
        calculated_bid = max(calculated_bid, DAILY_SALARY * 0.98)
    elif remaining_days <= 4:
        calculated_bid = max(calculated_bid, DAILY_SALARY * 0.9)

    final_bid = min(my_status['budget'], calculated_bid)

    if my_status['budget'] >= 1.0 and final_bid < 1.0:
        final_bid = 1.0
    elif my_status['budget'] == 0:
        final_bid = 0.0

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, 1.0 * WATER_REQ)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and prev.get('status') != 'error':
            yesterday_bids.append(prev['bid'])

    bid = DAILY_SALARY * 0.55

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_hp > 3:
                bid = DAILY_SALARY * 0.7
            else:
                bid = DAILY_SALARY * 0.95
        else:
            bid = max(DAILY_SALARY * 0.6, highest_prev_bid + 2.0)
    else:
        bid = DAILY_SALARY * 0.6

    if my_hp <= 2:
        bid = DAILY_SALARY * 0.98
    elif my_hp <= 4:
        bid = max(bid, DAILY_SALARY * 0.8)

    if my_no_water_days >= 1:
        bid = max(bid, DAILY_SALARY * 0.9)

    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2:
        bid = max(bid, DAILY_SALARY * 0.95)
    elif remaining_days <= 4:
        bid = max(bid, DAILY_SALARY * 0.85)

    if current_supply <= 18:
        bid = max(bid, DAILY_SALARY * 0.8)
    elif current_supply <= 21:
        bid = max(bid, DAILY_SALARY * 0.7)

    final_bid = min(my_budget, bid)

    if final_bid < 1.0 and my_budget > 0:
        final_bid = min(my_budget, 1.0 * WATER_REQ)
    elif final_bid < 0:
        final_bid = 0.0

    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From the Current Meta-Round State
    
    current_day = day_context['day']
    current_supply = day_context['supply']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimally to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    # Collect yesterday's bids for all alive opponents
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid
    # Starting point for a competitive bid, considering the high average bids of opponents
    base_bid = DAILY_SALARY * 0.75 # Default: 112.5

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP: bid very aggressively
        base_bid = DAILY_SALARY * 0.98 # Almost full salary
    elif my_status['hp'] <= 4: # Low HP: bid aggressively
        base_bid = DAILY_SALARY * 0.90
    elif my_status['hp'] >= 8: # Healthy HP: can afford to be less aggressive if competition allows
        base_bid = DAILY_SALARY * 0.65

    # Adjust bid based on opponent's previous highest bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were very aggressive yesterday, we need to be competitive
        if highest_prev_bid >= DAILY_SALARY * 0.8: # e.g., > 120
            if my_status['hp'] <= 4: # If I need water, try to outbid them
                base_bid = max(base_bid, highest_prev_bid + 3.0) # Slightly higher than highest prev bid
            else: # If healthy, still be competitive but don't overspend too much
                base_bid = max(base_bid, highest_prev_bid * 0.98) # Slightly below or match
        elif highest_prev_bid <= DAILY_SALARY * 0.5: # Opponents bid low yesterday (e.g., < 75)
            # Try to win cheaply, but ensure it's higher than their low bid
            base_bid = min(base_bid, highest_prev_bid + 5.0) # Win for a bit more than their low bid

    # Adjust bid based on supply scarcity
    # Supply range [15, 25]. WATER_REQ = 13.
    # If supply is 15, only one agent can get full water.
    # If supply is 25, almost two agents can get full water.
    if current_supply <= WATER_REQ + 2: # Very scarce (15-17 water)
        base_bid *= 1.1 # Increase bid to win scarce resources
    elif current_supply >= WATER_REQ * 2 - 2: # Abundant (24-25 water)
        base_bid *= 0.9 # Decrease bid if water is plentiful, try to save budget

    # Final bid must be within budget
    final_bid = min(my_status['budget'], base_bid)
    
    # Consider the day of the episode. Towards the end, agents might be more desperate.
    remaining_days = EPISODE_DAYS - current_day
    
    # If it's the last day or second to last day and HP is low, be very aggressive
    if remaining_days <= 2 and my_status['hp'] <= 4:
        final_bid = min(my_status['budget'], DAILY_SALARY * 1.05) # Allow slightly over salary to win
    
    # Ensure bid is at least a minimal amount to indicate participation
    final_bid = max(final_bid, DAILY_SALARY * 0.1) # Minimum bid of 15

    # General cap: don't bid more than salary unless it's an end-game desperate situation
    if final_bid > DAILY_SALARY and not (remaining_days <= 2 and my_status['hp'] <= 4):
        final_bid = DAILY_SALARY

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
    MIN_BID_IF_NO_COMPETITION = 1.0 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], MIN_BID_IF_NO_COMPETITION)

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.6 

    if my_hp <= 2: 
        base_bid = DAILY_SALARY * 0.98 
    elif my_hp <= 4: 
        base_bid = max(base_bid, DAILY_SALARY * 0.85) 
    elif my_hp <= 6: 
        base_bid = max(base_bid, DAILY_SALARY * 0.7) 
    
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.8: 
            if my_hp > 3: 
                base_bid = max(base_bid, DAILY_SALARY * 0.5) 
            else: 
                base_bid = max(base_bid, DAILY_SALARY * 0.95) 
        else: 
            base_bid = max(base_bid, highest_prev_bid + 5.0)
            base_bid = max(base_bid, DAILY_SALARY * 0.65) 

    if current_day >= EPISODE_DAYS - 2: 
        if my_hp <= 4:
            base_bid = max(base_bid, DAILY_SALARY * 0.99) 
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.8) 

    total_water_needed_by_all = WATER_REQ
    for opp in alive_opponents:
        total_water_needed_by_all += opp['water_requirement']
        
    if current_supply < total_water_needed_by_all:
        num_agents_can_satisfy = current_supply / WATER_REQ if WATER_REQ > 0 else 0
        
        if num_agents_can_satisfy < 2: 
            if my_hp <= 5: 
                base_bid = max(base_bid, DAILY_SALARY * 0.99) 
            else:
                base_bid = max(base_bid, DAILY_SALARY * 0.85) 
        elif current_supply < total_water_needed_by_all * 0.75:
             if my_hp <= 4:
                 base_bid = max(base_bid, DAILY_SALARY * 0.9)
             else:
                 base_bid = max(base_bid, DAILY_SALARY * 0.7)

    final_bid = min(my_budget, base_bid)
    
    final_bid = max(final_bid, 1.0) 

    return final_bid
"""
