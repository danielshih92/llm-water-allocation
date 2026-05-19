# ============================================================
# Experiment: exp_082
# Agent: Cindy
# Source: exp_082
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_supply = day_context['supply']
    current_day = day_context['day']

    # Base bid - a reasonable amount to secure water under normal conditions
    base_bid = DAILY_SALARY * 0.5 # Default: 75

    # Adjust bid based on HP and no-water-days for survival
    if my_hp <= 2: # Critical HP, bid very high
        base_bid = DAILY_SALARY * 0.95 # 142.5
    elif my_hp <= 4: # Low HP, bid high
        base_bid = DAILY_SALARY * 0.8 # 120
    
    if my_no_water_days >= 1: # Haven't gotten water recently, increase urgency
        base_bid += DAILY_SALARY * 0.1 # Add 15

    # Analyze opponents and total demand
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    total_water_needed_by_opponents = sum(o['water_requirement'] for o in alive_opponents)
    total_water_needed_overall = WATER_REQ + total_water_needed_by_opponents

    # Adjust bid based on supply scarcity
    if current_supply < total_water_needed_overall: # Supply is less than total demand, competition will be high
        scarce_factor = (total_water_needed_overall - current_supply) / total_water_needed_overall
        base_bid += DAILY_SALARY * 0.3 * scarce_factor # Max additional 45
    elif current_supply >= total_water_needed_overall * 1.5: # Abundant supply, can afford to bid lower
        base_bid -= DAILY_SALARY * 0.1 # Subtract 15
        base_bid = max(base_bid, DAILY_SALARY * 0.3) # Don't bid too low (min 45)

    # React to yesterday's bids if available (only from day 2 onwards)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)

        if max_yesterday_bid > DAILY_SALARY * 0.7: # Opponents bid high, indicates high competition/desperation
            base_bid = max(base_bid, max_yesterday_bid + 1) # Try to outbid the highest
        elif avg_yesterday_bid < DAILY_SALARY * 0.4: # Opponents bid low, try to get it cheaper but secure
            base_bid = min(base_bid, avg_yesterday_bid + 5) 
            base_bid = max(base_bid, DAILY_SALARY * 0.3) # Ensure a minimum reasonable bid
        else: # Moderate bids yesterday
            base_bid = max(base_bid, avg_yesterday_bid + (DAILY_SALARY * 0.05)) # Slightly above average to secure

    # Ensure bid is within budget and non-negative
    final_bid = min(my_budget, max(0.0, base_bid))
    
    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        # No opponents, bid conservatively to ensure water while saving budget
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    total_water_needed_for_all = WATER_REQ * (num_alive_opponents + 1)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Initialize base bid, similar to example's default
    base_bid = DAILY_SALARY * 0.55

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.85: # High competition detected yesterday
            if my_status['hp'] > 3: # My HP is good, can afford to be less aggressive
                base_bid = DAILY_SALARY * 0.3 # Try to save money
            else: # My HP is low, need water desperately
                base_bid = DAILY_SALARY * 0.95 # Bid aggressively
        else: # Moderate competition
            base_bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)
    
    # Adjust bid based on my HP and 'no_water_days'
    if my_status['hp'] <= 2: # Critical HP, must get water
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif my_status['no_water_days'] > 0: # Missed water yesterday, prioritize getting it today
        base_bid = max(base_bid, DAILY_SALARY * 0.75)

    # Adjust bid based on current day's supply scarcity
    current_supply = day_context['supply']
    if current_supply < total_water_needed_for_all: # Scarcity: not enough water for everyone
        # Increase bid, more so if scarcity is severe
        scarcity_factor = 1 + (total_water_needed_for_all - current_supply) / total_water_needed_for_all
        base_bid *= scarcity_factor
        
        # If supply is very low (e.g., only enough for 1-2 players), bid very aggressively
        if current_supply <= WATER_REQ * 2: 
            base_bid = max(base_bid, DAILY_SALARY * 0.98)
    else: # Abundant supply: enough water for everyone
        # If there's plenty of water, cap bid to save budget, but ensure it's still competitive
        base_bid = min(base_bid, DAILY_SALARY * 0.7)

    # Ensure bid does not exceed available budget
    final_bid = min(my_status['budget'], base_bid)
    
    # Ensure bid is at least 1.0 to participate, unless budget is 0
    final_bid = max(1.0, final_bid) if my_status['budget'] > 0 else 0.0

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

    # Determine how many agents can get water today (given supply range and water_req, this will almost always be 1)
    num_possible_winners = int(day_context['supply'] / WATER_REQ)

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimally to secure water.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Collect yesterday's bids and identify Eric's status
    yesterday_bids = []
    eric_alive = False
    eric_prev_bid = 0.0

    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
            if opp_id == "Eric":
                eric_alive = True
                if prev and prev.get('bid') is not None:
                    eric_prev_bid = prev['bid']

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Determine bid based on urgency and opponent behavior
    bid_value = 0.0

    # Urgency factors
    is_critical_hp = my_status['hp'] <= 3
    is_critical_no_water = my_status['no_water_days'] >= 2 # Can afford 1 more day without losing HP
    is_late_game = day_context['day'] >= EPISODE_DAYS - 2 # Last 2 days are critical

    if eric_alive and eric_prev_bid > 0:
        # Eric is the strongest opponent. React strongly to him.
        if is_critical_hp or is_critical_no_water or is_late_game:
            # Must win this day
            bid_value = max(DAILY_SALARY * 1.3, eric_prev_bid + 15)
        else:
            # Not critical, but Eric is a threat. Try to outbid him.
            # If Eric's bid was very high, we might still need to match.
            bid_value = max(DAILY_SALARY * 1.05, eric_prev_bid + 5)
    else:
        # Eric is not a direct factor (dead or no recent bid). React to other opponents.
        if is_critical_hp or is_critical_no_water or is_late_game:
            # Must win this day
            bid_value = max(DAILY_SALARY * 1.2, highest_prev_bid + 10)
        else:
            # Normal day, try to win without overspending too much.
            bid_value = max(DAILY_SALARY * 0.9, highest_prev_bid + 1)

    # Ensure bid does not exceed current budget
    final_bid = min(bid_value, my_status['budget'])

    # Ensure bid is at least a minimal amount if budget allows, to signal intent, unless budget is zero
    if final_bid == 0 and my_status['budget'] > 0:
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Calculate base bid adjusted for supply scarcity
    # When supply is MIN_SUPPLY (15), supply_ratio = 0, base_bid is higher
    # When supply is MAX_SUPPLY (25), supply_ratio = 1, base_bid is lower
    supply_ratio = (day_context['supply'] - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio)) # Clamp ratio between 0 and 1
    
    # Base bid: higher when supply is scarce (0.7 * DAILY_SALARY), lower when abundant (0.3 * DAILY_SALARY)
    base_bid = DAILY_SALARY * (0.7 - supply_ratio * 0.4) 

    # If no alive opponents, bid low to save budget
    if not alive_opponents:
        return min(my_status['budget'], base_bid * 0.6)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_bid = base_bid # Start with the supply-adjusted base bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents are bidding very high (e.g., >= 85% of daily salary)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # If my HP is good, try to save
                current_bid = DAILY_SALARY * 0.3 
            else: # If my HP is low, I must compete aggressively
                current_bid = DAILY_SALARY * 0.95 
        # If opponents are bidding moderately or low
        else:
            # Bid slightly above the highest previous bid, but at least the base_bid
            current_bid = max(base_bid, highest_prev_bid + 1.5)
            
            # If supply is tight (below average or total water needed > supply), ensure a decent bid
            # Average supply is (15+25)/2 = 20
            if day_context['supply'] < 20.0 or (len(alive_opponents) + 1) * WATER_REQ > day_context['supply']:
                current_bid = max(current_bid, DAILY_SALARY * 0.6)
    else: # No previous bids from opponents, just use base_bid and consider supply tightness
        current_bid = base_bid
        if day_context['supply'] < 20.0 or (len(alive_opponents) + 1) * WATER_REQ > day_context['supply']:
            current_bid = max(current_bid, DAILY_SALARY * 0.6)

    # If my HP is critically low, prioritize survival above all else
    if my_status['hp'] <= 2:
        current_bid = DAILY_SALARY * 0.95 

    # Ensure the bid does not exceed available budget and is at least 1.0
    final_bid = min(my_status['budget'], current_bid)
    return max(1.0, final_bid)
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
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_active_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None and prev['bid'] > 0:
                yesterday_active_bids.append(prev['bid'])

    current_bid = DAILY_SALARY * 0.5

    if yesterday_active_bids:
        highest_prev_bid = max(yesterday_active_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 2:
                current_bid = min(my_status['budget'], highest_prev_bid * 0.95)
            else:
                current_bid = min(my_status['budget'], highest_prev_bid * 1.05 + 1)
        elif highest_prev_bid > DAILY_SALARY * 0.3:
            current_bid = max(current_bid, highest_prev_bid + 1.0)

    if my_status['hp'] <= 2:
        current_bid = max(current_bid, DAILY_SALARY * 0.95)
    elif my_status['no_water_days'] > 0:
        current_bid = max(current_bid, DAILY_SALARY * 0.8)

    days_left = EPISODE_DAYS - day_context['day']
    if days_left <= 2:
        current_bid = max(current_bid, DAILY_SALARY * 0.75)

    num_water_units_from_supply = int(day_context['supply'] // WATER_REQ)
    num_potential_bidders = len(alive_opponents) + 1

    if num_water_units_from_supply >= num_potential_bidders:
        if my_status['hp'] > 3:
            current_bid = min(current_bid, DAILY_SALARY * 0.4)
    elif num_water_units_from_supply < num_potential_bidders and num_water_units_from_supply > 0:
        current_bid = max(current_bid, DAILY_SALARY * 0.6)
    else:
        if my_status['hp'] <= 2:
            current_bid = max(current_bid, DAILY_SALARY * 0.98)
        else:
            current_bid = min(current_bid, DAILY_SALARY * 0.6)

    final_bid = max(0.0, min(my_status['budget'], current_bid))
    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid a minimal amount to get water
    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid strategy:
    # Aggressive if critical, moderate otherwise.
    target_bid = DAILY_SALARY * 0.6 # Default moderate bid (90)

    if my_status['no_water_days'] > 0:
        target_bid = DAILY_SALARY * 0.95 # Very high if deprived (142.5)
    elif my_status['hp'] <= 2:
        target_bid = DAILY_SALARY * 0.9 # Critical HP (135)
    elif my_status['hp'] <= 4:
        target_bid = DAILY_SALARY * 0.75 # Low HP (112.5)

    current_bid = target_bid

    # Adjust bid based on opponent's previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        bid_to_beat = highest_prev_bid + 1.0 # Try to beat the highest bid

        if my_status['no_water_days'] > 0 or my_status['hp'] <= 4:
            # Critical condition: bid very aggressively, ensuring we try to beat it
            current_bid = max(target_bid, bid_to_beat)
            if bid_to_beat > DAILY_SALARY * 0.95: # If opponents are bidding almost max salary
                current_bid = max(current_bid, DAILY_SALARY * 0.98) # Bid even higher
        else:
            # Not critical: bid above previous, but with some budget consideration
            current_bid = max(target_bid, bid_to_beat)
            if highest_prev_bid >= DAILY_SALARY * 0.85: # Opponents are bidding very high (>= 127.5)
                # If healthy, cap bid to save budget, but still try to win
                current_bid = min(current_bid, DAILY_SALARY * 0.9) # Cap at 135 if healthy
                if my_status['hp'] > 6 and day_context['day'] < 8: # If very healthy and early days
                    current_bid = min(current_bid, DAILY_SALARY * 0.7) # Back off more (105)
    
    # Ensure bid is within budget and at least 1.0
    final_bid = min(my_status['budget'], current_bid)
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to secure water and save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Base bid: Start with a strong bid, as competition for full water is always high.
    # Aim for a profit while being competitive.
    bid_amount = DAILY_SALARY * 0.80

    # Adjust bid based on my current HP
    if my_status['hp'] <= 2: # Critical HP, must win
        bid_amount = DAILY_SALARY * 0.99 # Bid very aggressively, almost full salary
    elif my_status['hp'] <= 4: # Low HP, bid aggressively
        bid_amount = DAILY_SALARY * 0.90
    elif my_status['hp'] >= 8 and day_context['day'] < EPISODE_DAYS / 2: # Healthy HP in early game, can be slightly less aggressive
        bid_amount = DAILY_SALARY * 0.75

    # React to opponents' previous bids to stay competitive
    yesterday_competitive_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            # Consider bids that were high enough to indicate a competitive intent
            # or if they successfully won water, regardless of the bid amount.
            if prev.get('status') == 'won' or prev['bid'] >= DAILY_SALARY * 0.6:
                yesterday_competitive_bids.append(prev['bid'])

    if yesterday_competitive_bids:
        highest_prev_bid = max(yesterday_competitive_bids)
        # If the highest bid yesterday was very high, slightly outbid it.
        if highest_prev_bid >= DAILY_SALARY * 0.95:
            bid_amount = max(bid_amount, highest_prev_bid + 2.0)
        # If it was moderately high, outbid it by a smaller margin.
        elif highest_prev_bid >= DAILY_SALARY * 0.80:
            bid_amount = max(bid_amount, highest_prev_bid + 1.5)
        # If opponents were not very aggressive, ensure my bid is still higher but don't overpay.
        else:
            bid_amount = max(bid_amount, highest_prev_bid + 1.0)
    
    # End-game strategy: Become more desperate to survive in the final days
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days
        if my_status['hp'] <= 3: # Critical HP in end-game, bid whatever it takes
            bid_amount = max(bid_amount, DAILY_SALARY * 1.05) # Potentially go into debt
        elif my_status['hp'] <= 5: # Low HP in end-game
            bid_amount = max(bid_amount, DAILY_SALARY * 0.95)
        else: # Healthy HP in end-game, still ensure win
            bid_amount = max(bid_amount, DAILY_SALARY * 0.88)

    # Ensure the bid does not exceed current budget, unless extremely desperate (low HP, end game)
    # If budget is very low and HP is critical, bid entire budget to maximize survival chance
    if my_status['hp'] <= 2 and day_context['day'] >= EPISODE_DAYS - 2:
        final_bid = my_status['budget']
    else:
        final_bid = min(my_status['budget'], max(1.0, bid_amount))

    # Return the bid formatted to two decimal places
    return float(f"{final_bid:.2f}")
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.55
    bid = base_bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            if my_hp <= 3:
                bid = DAILY_SALARY * 0.98
            elif my_hp <= 5:
                bid = max(base_bid, highest_prev_bid + 2.0)
            else:
                bid = max(base_bid, highest_prev_bid + 1.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.7:
            if my_hp <= 4:
                bid = max(base_bid, highest_prev_bid + 3.0)
            else:
                bid = max(base_bid, highest_prev_bid + 1.5)
        else:
            if my_hp <= 2:
                bid = DAILY_SALARY * 0.95
            elif my_hp <= 4:
                bid = DAILY_SALARY * 0.85
            else:
                bid = max(base_bid, highest_prev_bid + 1.0)
    else:
        if my_hp <= 2:
            bid = DAILY_SALARY * 0.95
        elif my_hp <= 4:
            bid = DAILY_SALARY * 0.85
        else:
            bid = base_bid

    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2:
        if my_hp <= 5:
            bid = max(bid, DAILY_SALARY * 0.95)
        elif my_hp <= 7:
            bid = max(bid, DAILY_SALARY * 0.8)
    elif remaining_days <= 4:
        if my_hp <= 4:
            bid = max(bid, DAILY_SALARY * 0.9)

    final_bid = min(bid, my_budget)
    
    if final_bid <= 0 and my_budget > 0:
        final_bid = 1.0
    elif final_bid <= 0 and my_budget <= 0:
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
    EPISODE_DAYS = 10

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    active_opponents_count = 0
    alex_status = None
    for agent_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            active_opponents_count += 1
            if agent_id == "Alex":
                alex_status = opp_data

    # If I am the only active agent or only very weak opponents remain (e.g. no Alex or Alex is dead)
    if active_opponents_count == 0 or (active_opponents_count == 1 and alex_status is None) or (alex_status and not alex_status['alive']):
        return min(my_budget, 1.0) # Bid a minimal amount to secure water

    alex_prev_bid = 0.0
    if alex_status and alex_status.get('previous_trace') and alex_status['previous_trace'].get('bid') is not None:
        alex_prev_bid = alex_status['previous_trace']['bid']

    target_bid = 0.0
    if my_hp <= 2: # Desperate for water
        # Aggressive bid, targeting above Alex's historical max (93.5) and a high percentage of salary
        target_bid = max(alex_prev_bid + 5.0, 95.0, DAILY_SALARY * 0.75)
    elif my_hp >= 4: # Can afford to be conservative
        # Conservative bid, targeting above Alex's historical average (60.954) and a moderate percentage of salary
        target_bid = max(alex_prev_bid + 1.0, 65.0, DAILY_SALARY * 0.45)
    else: # Normal HP (3)
        # Moderate bid, targeting a solid percentage of salary and slightly above Alex's previous
        target_bid = max(alex_prev_bid + 2.0, 80.0, DAILY_SALARY * 0.6)

    # Adjust bid based on the day (later days, higher stakes)
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        target_bid = max(target_bid, DAILY_SALARY * 0.85) # Ensure high bid towards the end
    elif current_day >= EPISODE_DAYS // 2: # Mid-game
        target_bid = max(target_bid, DAILY_SALARY * 0.7)

    # Ensure bid is within my budget and non-negative
    final_bid = min(my_budget, target_bid)
    final_bid = max(0.0, final_bid)

    # If budget is critically low and I'm desperate, bid everything
    if my_budget < DAILY_SALARY * 0.5 and my_hp <= 1:
        final_bid = my_budget

    return final_bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents are bidding very high (e.g., Alex's aggressive bids)
        if highest_prev_bid >= DAILY_SALARY * 0.85: # 127.5
            if my_status['hp'] > 3:
                # If HP is good, consider backing off to save budget and let opponents overspend
                return min(my_status['budget'], DAILY_SALARY * 0.3) # 45
            # If HP is critical, bid high for survival
            return min(my_status['budget'], DAILY_SALARY * 0.95) # 142.5
        
        # If opponents are bidding moderately, bid slightly above to win
        return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)) # Base 75, then +1.5

    # Default bid if no previous bids or specific conditions met
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.9) # 135 (Survival bid)
    return min(my_status['budget'], DAILY_SALARY * 0.55) # 82.5 (Standard competitive bid)
"""
