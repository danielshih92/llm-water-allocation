# ============================================================
# Experiment: exp_111
# Agent: Cindy
# Source: exp_111
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

    # If I'm the last one standing, bid minimal to save budget.
    if num_alive_opponents == 0:
        return min(my_status['budget'], 1.0)

    # 1. Look at yesterday's situation (Trace) for all active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Determine my bid based on my HP, budget, and opponent's last actions.

    # Critical HP: If my HP is very low, bid very high to survive.
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # Low HP: If my HP is low, bid high.
    if my_status['hp'] <= 4:
        # If opponents bid high yesterday, I need to match or slightly exceed.
        if highest_prev_bid >= DAILY_SALARY * 0.7:
            return min(my_status['budget'], highest_prev_bid + 5)
        # Otherwise, bid a solid amount to secure water.
        return min(my_status['budget'], DAILY_SALARY * 0.75)

    # Moderate/Healthy HP: More flexible.
    # Consider current supply vs demand.
    current_supply = day_context['supply']
    # If supply is tight (e.g., less than enough for everyone)
    if current_supply < WATER_REQ * (num_alive_opponents + 1):
        # Competition is likely.
        # If yesterday's highest bid was significant, slightly outbid it.
        if highest_prev_bid >= DAILY_SALARY * 0.5:
            return min(my_status['budget'], highest_prev_bid + 2)
        # Otherwise, bid a reasonable amount to secure water.
        return min(my_status['budget'], DAILY_SALARY * 0.6)
    else:
        # Supply is relatively abundant.
        # If yesterday's bids were high, maybe opponents are bluffing or desperate.
        # If I have good HP, I can try to bid a bit lower to save money.
        if highest_prev_bid >= DAILY_SALARY * 0.7:
            return min(my_status['budget'], DAILY_SALARY * 0.5)
        # If bids were generally low or moderate, bid slightly above average or a safe amount.
        return min(my_status['budget'], max(DAILY_SALARY * 0.4, highest_prev_bid + 1))

    # Fallback / Default bid (should be caught by previous conditions)
    return min(my_status['budget'], DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Strategy 1: If I'm the only one left, bid minimal to save budget
    if not alive_opponents:
        return min(my_budget, 1.0)

    # Strategy 2: Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Strategy 3: Determine bid based on my HP and opponent behavior
    bid = 0.0 # Initialize bid

    # Base bid: a reasonable amount to secure water
    # Adjust based on how many opponents and how scarce water is
    total_expected_demand = WATER_REQ + sum(o['water_requirement'] for o in alive_opponents)

    if total_expected_demand > current_supply:
        # Water is scarce, bid more aggressively
        base_bid_multiplier = 0.6
    else:
        # Water is abundant, can bid less aggressively
        base_bid_multiplier = 0.45

    bid = DAILY_SALARY * base_bid_multiplier

    # High priority: If my HP is critical, bid very high
    if my_hp <= 2:
        bid = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP, bid high
        bid = DAILY_SALARY * 0.8
    elif my_hp <= 6 and my_status['no_water_days'] > 0: # If I missed water recently and HP is not great
        bid = DAILY_SALARY * 0.75

    # Adjust bid based on yesterday's highest opponent bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If opponents were very aggressive yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_hp > 5: # If healthy, I can try to conserve or match
                bid = max(bid, highest_prev_bid * 0.95) # Slightly less than their max, hoping they lower
            else: # Not healthy, must compete strongly
                bid = max(bid, highest_prev_bid + 2.0) # Slightly exceed to ensure win
        # If opponents were moderately aggressive
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            bid = max(bid, highest_prev_bid + 1.0) # Try to win by a small margin
        # If opponents were generally low bidders
        else:
            bid = max(bid, highest_prev_bid + 0.5) # Just slightly above their highest low bid

    # Ensure bid is never more than current budget
    final_bid = min(my_budget, bid)

    # If I'm critical and have budget, ensure a high bid
    if my_hp <= 2 and my_budget > 0:
        final_bid = min(my_budget, max(final_bid, DAILY_SALARY * 0.95))
    # If bid became too low but I have budget, set a minimum to avoid bidding 0 by accident
    elif final_bid < 1.0 and my_budget > 0:
        final_bid = max(1.0, final_bid)

    # If I'm very low on budget and it's not critical HP, try to save
    if my_budget < DAILY_SALARY * 1.5 and my_hp > 4:
        final_bid = min(final_bid, DAILY_SALARY * 0.4)

    # Ensure the bid is a float and formatted to two decimal places.
    return float(f"{final_bid:.2f}")
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
    
    # If no opponents, bid low to save budget, but ensure water.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Critical survival logic: If HP is very low, bid very aggressively
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were very aggressive yesterday (e.g., Alex)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # If I have healthy HP, try to conserve a bit
                return min(my_status['budget'], DAILY_SALARY * 0.4)
            else: # If HP is low but not critical (handled above if <=2), still need to be aggressive
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else:
            # If highest bid was moderate or low, try to win for slightly more
            return min(my_status['budget'], max(DAILY_SALARY * 0.55, highest_prev_bid + 2))
    
    # If no previous bids from alive opponents (e.g., Day 1 or all previous bidders died/didn't bid)
    return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    # --- Step 1: Determine base bid based on self-preservation and game state ---
    provisional_bid = 0.0

    # HP-based aggressiveness
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        provisional_bid = DAILY_SALARY * 0.95 # Critical: must get water
    elif my_status['hp'] <= 4:
        provisional_bid = DAILY_SALARY * 0.80 # High pressure
    elif my_status['hp'] <= 7:
        provisional_bid = DAILY_SALARY * 0.65 # Medium pressure
    else:
        provisional_bid = DAILY_SALARY * 0.55 # Comfortable

    # Adjust for day progress: increase bid towards the end of the episode
    day_progress_factor = day_context['day'] / EPISODE_DAYS
    provisional_bid += DAILY_SALARY * 0.1 * day_progress_factor

    # Adjust for supply scarcity: increase bid if supply is low
    supply_normalized = (day_context['supply'] - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_pressure_factor = 1 - supply_normalized # 1 for min supply, 0 for max supply
    provisional_bid += DAILY_SALARY * 0.15 * supply_pressure_factor

    # --- Step 2: React to opponents' yesterday bids ---
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were very aggressive yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 6: # If I have good HP, be conservative, let them overspend
                provisional_bid = min(provisional_bid, DAILY_SALARY * 0.4)
            else: # My HP is not great, I need to compete
                provisional_bid = max(provisional_bid, highest_prev_bid + 1.0)
        # If opponents were moderately aggressive, but higher than my provisional
        elif highest_prev_bid > provisional_bid * 0.9:
            if my_status['hp'] <= 4 or my_status['no_water_days'] > 0: # I'm under pressure
                provisional_bid = max(provisional_bid, highest_prev_bid + 0.5)
            else: # I'm not under critical pressure, but want to stay competitive
                provisional_bid = max(provisional_bid, highest_prev_bid * 0.98)

    # --- Step 3: Final bid constraints ---
    final_bid = provisional_bid

    # Ensure bid is not negative
    final_bid = max(0.0, final_bid)
    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], final_bid)
    # Cap bid at a reasonable maximum (e.g., 110% of daily salary) to prevent overspending
    final_bid = min(final_bid, DAILY_SALARY * 1.1)

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
    
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_supply = day_context['supply']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    supply_aggression_multiplier = 1.0 + (1 - (current_supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)) * 0.2
    
    # Initialize bid with a conservative value, adjusted by supply
    calculated_bid = DAILY_SALARY * 0.55 * supply_aggression_multiplier

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were very aggressive yesterday (bid high)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_hp > 3:
                # My HP is relatively good, can afford to save
                calculated_bid = min(DAILY_SALARY * 0.3 * supply_aggression_multiplier, highest_prev_bid * 0.9)
                calculated_bid = max(calculated_bid, DAILY_SALARY * 0.4)
            else:
                # My HP is critical, must secure water
                calculated_bid = max(highest_prev_bid * 1.05, DAILY_SALARY * 0.95 * supply_aggression_multiplier)
        
        # Opponents were moderately aggressive or less
        else:
            # Try to slightly outbid the highest previous bid, but ensure a minimum competitive bid
            calculated_bid = max(highest_prev_bid + 1.5, DAILY_SALARY * 0.5 * supply_aggression_multiplier)
    
    # If no previous bids from alive opponents (e.g., first day or all new opponents)
    else:
        if my_hp <= 2:
            # My HP is critical, bid high
            calculated_bid = DAILY_SALARY * 0.9 * supply_aggression_multiplier
        else:
            # HP is good, bid moderately
            calculated_bid = DAILY_SALARY * 0.55 * supply_aggression_multiplier

    # End-game adjustment: If few days left and HP is low, bid very aggressively
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_hp <= 3:
        calculated_bid = max(calculated_bid, DAILY_SALARY * 1.05)

    # Final bid must not exceed budget and have a reasonable minimum
    final_bid = min(my_budget, max(DAILY_SALARY * 0.2, calculated_bid))

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
    
    if not alive_opponents:
        # No competition, bid low to save budget but ensure water
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base competitive bid, considering strong opponents like Alex and Eric
    # who bid around 70% of a similar daily salary (150 * 0.7 = 105)
    base_competitive_bid = DAILY_SALARY * 0.7

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # Adjust base bid based on highest previous bid to stay competitive
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Very aggressive previous bid
            base_competitive_bid = max(base_competitive_bid, highest_prev_bid + 3)
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # Moderately aggressive previous bid
            base_competitive_bid = max(base_competitive_bid, highest_prev_bid + 1)
        else: # Low previous bid, still aim to win but save money
            base_competitive_bid = max(base_competitive_bid, highest_prev_bid + 0.5)
    
    # Adjust bid based on my HP
    bid = base_competitive_bid # Start with the calculated competitive bid

    if my_status['hp'] <= 3: # Critical HP, must get water
        bid = max(bid, DAILY_SALARY * 0.95) # Bid very aggressively
    elif my_status['hp'] <= 5: # Low HP, need water
        bid = max(bid, DAILY_SALARY * 0.8) # Bid aggressively
    
    # Adjust bid based on supply scarcity
    num_full_requirements_possible = int(day_context['supply'] // WATER_REQ) # CRITICAL INDEX RULE
    
    if num_full_requirements_possible == 0: # Supply less than my requirement
        # No point in bidding high for full requirement, bid minimally.
        bid = min(my_status['budget'], DAILY_SALARY * 0.05) # Very low bid
    elif num_full_requirements_possible == 1 and len(alive_opponents) >= 1: # Only one player can get full water
        # Extreme competition, bid very high
        bid = max(bid, DAILY_SALARY * 0.9)
    elif num_full_requirements_possible < len(alive_opponents) + 1: # Not everyone can get full water
        # High competition, increase bid
        bid = max(bid, DAILY_SALARY * 0.75)
    else: # Supply is relatively abundant, everyone can potentially get water
        # Can be slightly less aggressive to save budget
        bid = bid * 0.95 # Reduce bid slightly

    # Final bid must be within budget and at least a minimal amount
    bid = min(my_status['budget'], bid)
    bid = max(bid, 1.0) # Ensure bid is at least 1.0

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
    
    # Base bid - a moderate amount
    bid = DAILY_SALARY * 0.65 # A reasonable starting point

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimum to win
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1) # Bid low if no competition

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Get highest previous bid from opponents
    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # --- Bidding Logic ---

    # 1. Emergency: Low HP or missed water yesterday
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        bid = DAILY_SALARY * 0.95 # Bid very aggressively
        if highest_prev_bid > bid: # If opponents were even more aggressive
            bid = highest_prev_bid + 5.0 # Try to outbid them

    # 2. React to high opponent bids from yesterday
    elif highest_prev_bid >= DAILY_SALARY * 0.85: # Opponents were very aggressive
        if my_status['hp'] > 3: # If I'm healthy, I can afford to be slightly less aggressive
            bid = DAILY_SALARY * 0.75 # Still competitive but not overspending
        else: # Not healthy, need to win
            bid = highest_prev_bid + 2.0 # Slightly above their highest to win

    # 3. React to moderate opponent bids from yesterday
    elif highest_prev_bid > 0.0: # If there were previous bids, but not extremely high
        bid = max(bid, highest_prev_bid + 1.0) # Bid slightly above their highest

    # 4. Supply scarcity adjustment
    # Total water needed by all active participants (including me)
    total_water_needed = (num_alive_opponents + 1) * WATER_REQ
    
    # If supply is less than total water needed, it's a scarcity situation
    if day_context['supply'] < total_water_needed:
        # The more scarce, the higher the bid
        if day_context['supply'] < total_water_needed * 0.75: # Very scarce
            bid *= 1.2
        elif day_context['supply'] < total_water_needed: # Moderately scarce
            bid *= 1.1

    # 5. End game strategy: Be more aggressive on the last few days
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days
        bid = max(bid, DAILY_SALARY * 1.05) # Ensure high bid to survive

    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], bid)
    
    # Ensure a minimum bid of 1.0 if budget is available and the calculated bid is non-positive
    if final_bid <= 0.0 and my_status['budget'] > 0.0:
        final_bid = 1.0
    
    # Ensure bid is not negative
    final_bid = max(0.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_BID = 1.0 # Minimum bid to ensure positive bid

    # Ensure budget is not exceeded
    max_possible_bid = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # --- Phase 1: Handle extreme cases ---
    # If no opponents are alive, bid minimal to save budget
    if not alive_opponents:
        return min(max_possible_bid, DAILY_SALARY * 0.1) # Bid 10% of salary

    # If my HP is critically low, bid very aggressively to survive
    if my_status['hp'] <= 2:
        return min(max_possible_bid, DAILY_SALARY * 0.95) # Bid 95% of salary (142.5)

    # --- Phase 2: Analyze opponent's previous bids ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    else:
        # If no previous bids, assume a moderate baseline competition
        highest_prev_bid = DAILY_SALARY * 0.5 # 75

    # --- Phase 3: Dynamic bidding based on opponent behavior and HP ---
    current_bid = 0.0

    # Scenario 1: Opponents were very aggressive yesterday
    if highest_prev_bid >= DAILY_SALARY * 0.85: # Opponent bid >= 127.5
        # If my HP is good (4 or more), consider retreating to let others overspend
        if my_status['hp'] > 3:
            current_bid = DAILY_SALARY * 0.3 # Retreat bid (45)
        else: # My HP is somewhat low (3), still need to compete strongly
            current_bid = max(DAILY_SALARY * 0.75, highest_prev_bid + 1.0) # Bid around 112.5 or slightly above opponent
    # Scenario 2: Opponents were moderately aggressive or less
    else:
        # Bid slightly above their highest previous bid, but at least a base amount
        current_bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5) # Bid at least 75, or slightly above max opponent bid

    # --- Phase 4: Adjust for supply scarcity ---
    # Supply range is [15, 25]. My WATER_REQ is 13. Water is always competitive.
    if day_context['supply'] <= 17.0: # Low supply (15, 16, 17)
        current_bid *= 1.1 # Increase bid by 10%
    elif day_context['supply'] >= 23.0: # High supply (23, 24, 25)
        current_bid *= 0.95 # Decrease bid by 5%

    # --- Phase 5: Final checks ---
    final_bid = min(current_bid, max_possible_bid)
    return max(MIN_BID, final_bid)
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid minimally to save budget, but ensure water acquisition.
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    
    # Cindy's HP is always critical (10 HP, needs 13 water to survive). She must always secure water.
    
    # Base bid: High to ensure survival, starting above Bob's average and competitive with Alex's max.
    base_bid = DAILY_SALARY * 0.8 
    
    # Adjust based on opponent's yesterday's bids
    if highest_prev_bid > 0:
        # If the highest bid was very high (e.g., Alex's max), bid slightly above it.
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, highest_prev_bid + 5)
        # If it was moderately high (e.g., Bob's range), ensure we still bid strongly.
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            base_bid = max(base_bid, highest_prev_bid + 2)
    
    # Adjust for supply scarcity: Lower supply means higher competition for critical water.
    if current_supply <= WATER_REQ: # Only enough for one agent to get 13 units
        base_bid = max(base_bid, DAILY_SALARY * 0.95) # Bid very aggressively
    elif current_supply < WATER_REQ * 2: # Enough for one, maybe some for a second
        base_bid = max(base_bid, DAILY_SALARY * 0.85)

    # Adjust for day progression: Be more aggressive towards the end if still in contention.
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        base_bid = max(base_bid, DAILY_SALARY * 0.98) # Almost full salary
        # If it's the very last day and I need water, go almost all in.
        if current_day == EPISODE_DAYS:
            base_bid = max(base_bid, my_budget * 0.99)

    # Final bid cannot exceed current budget.
    final_bid = min(my_budget, base_bid)
    
    # Ensure a minimum bid of 1 to always participate, unless budget is 0.
    final_bid = max(final_bid, 1)

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid a safe, low amount to get water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Critical HP: Must get water at almost any cost (within budget)
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 1.4) # Aggressive to match high bidders

    # Get yesterday's bids from alive opponents
    yesterday_bids = []
    alex_alive = False
    eric_alive = False
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            if opp_id == "Alex":
                alex_alive = True
            if opp_id == "Eric":
                eric_alive = True
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    current_supply = day_context['supply']
    current_day = day_context['day']

    # Base bid: a fraction of daily salary
    base_bid = DAILY_SALARY * 0.6

    # If supply is low, competition is higher. Increase base bid.
    if current_supply <= MIN_SUPPLY + 2: # e.g., 15, 16, 17
        base_bid = DAILY_SALARY * 0.8
        if my_status['hp'] <= 5: # More aggressive if HP is somewhat low on low supply days
             base_bid = DAILY_SALARY * 1.0

    # If Alex or Eric are alive and bid high yesterday, we need to be competitive
    if (alex_alive or eric_alive) and highest_prev_bid > DAILY_SALARY * 0.9: # If they bid > 135
        # Try to outbid them, but cap to avoid excessive spending if their salary is much higher
        competitive_bid = min(highest_prev_bid * 1.05, DAILY_SALARY * 1.5) # Bid slightly higher, but capped
        base_bid = max(base_bid, competitive_bid)
    elif highest_prev_bid > 0: # If other opponents bid, be slightly higher
        base_bid = max(base_bid, highest_prev_bid + 5)

    # Adjust bid based on remaining days - become more aggressive towards the end
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 3: # Last few days
        if my_status['hp'] <= 5: # If HP is low and near end
            base_bid = max(base_bid, DAILY_SALARY * 1.3) # Very aggressive
        else:
            base_bid = max(base_bid, DAILY_SALARY * 1.0) # Aggressive even if HP is good

    # Ensure bid doesn't exceed budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure bid is at least a small positive value if budget allows and calculated bid is zero or less
    if final_bid <= 0 and my_status['budget'] > 0:
        return 1.0 

    return final_bid
"""
