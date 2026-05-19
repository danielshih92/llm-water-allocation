# ============================================================
# Experiment: exp_046
# Agent: Cindy
# Source: exp_046
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # 1. If I'm the only one left, bid minimally to survive.
    if num_alive_opponents == 0:
        return min(my_status['budget'], 1)

    current_supply = day_context['supply']
    day = day_context['day']

    # Base bid: a sensible default for my water requirement
    base_bid = DAILY_SALARY * 0.65 # Start with a moderate bid

    # 2. Critical HP (my_status['hp'] <= 2): Bid aggressively to survive.
    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP, but not critical
        base_bid = DAILY_SALARY * 0.8

    # 3. Adjust based on supply scarcity and total water needed
    total_water_needed_by_all = WATER_REQ + sum(o['water_requirement'] for o in alive_opponents)
    
    if current_supply < total_water_needed_by_all: # Supply is tight for everyone
        base_bid *= 1.15
    elif current_supply > total_water_needed_by_all + WATER_REQ: # Supply is quite abundant
        base_bid *= 0.85

    # 4. Observe yesterday's bids from opponents to adapt.
    yesterday_bids = []
    opponent_critical_hps = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
        if opp['hp'] <= 2:
            opponent_critical_hps.append(opp)

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents bid very high yesterday, be prepared to bid higher
        if max_yesterday_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, max_yesterday_bid + 5) # Try to outbid by a small margin

        # If average bids were low, maybe I can save money
        elif avg_yesterday_bid <= DAILY_SALARY * 0.5:
            base_bid = min(base_bid, avg_yesterday_bid + 10) # Don't overbid too much

    # 5. Target critical opponents if I have an advantage (enough HP, budget)
    if opponent_critical_hps and my_status['hp'] > 2 and my_status['budget'] > DAILY_SALARY:
        # If I can afford it and they are weak, try to outbid them decisively
        base_bid = max(base_bid, DAILY_SALARY * 0.98) # Very aggressive bid

    # Final bid must be within budget and non-negative
    final_bid = max(1, min(my_status['budget'], base_bid))

    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents are alive, bid minimally to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid multiplier based on HP
    if my_status['hp'] <= 2: # Critical HP, must win
        bid_multiplier = 0.95 # Bid very aggressively
    elif my_status['hp'] <= 4: # Low HP, need water
        bid_multiplier = 0.75
    else: # Healthy HP
        bid_multiplier = 0.6 # Competitive but not overly aggressive

    base_bid = DAILY_SALARY * bid_multiplier

    # Adjust bid based on opponent's previous bids
    if yesterday_bids:
        max_opp_bid = max(yesterday_bids)
        # If my base bid is lower than max opponent bid, try to outbid it
        # Add a small buffer to ensure outbidding
        if base_bid < max_opp_bid + 5:
            base_bid = max_opp_bid + 5
            
        # Cap the bid to prevent overspending when not absolutely critical
        if my_status['hp'] > 4 and base_bid > DAILY_SALARY * 0.8:
            base_bid = DAILY_SALARY * 0.8
        elif my_status['hp'] <= 4 and my_status['hp'] > 2 and base_bid > DAILY_SALARY * 0.9:
            base_bid = DAILY_SALARY * 0.9
        elif my_status['hp'] <= 2 and base_bid > DAILY_SALARY * 0.98: # Allow very high bids for critical HP
            base_bid = DAILY_SALARY * 0.98

    # Minimum bid to stay competitive, given tight supply
    min_competitive_bid = DAILY_SALARY * 0.4 
    base_bid = max(base_bid, min_competitive_bid)

    # Final bid is capped by current budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure bid is positive
    final_bid = max(0.1, final_bid)

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # --- Survival Logic ---
    # If HP is critically low (e.g., 2 or less) or I missed water yesterday, bid very aggressively.
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        return min(my_status['budget'], DAILY_SALARY * 0.98) # Bid almost full salary

    # --- No Opponents ---
    if not alive_opponents:
        # If no one else is bidding, bid very low to save money.
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # --- Opponent Analysis and Dynamic Bidding ---
    yesterday_bids = []
    total_opponent_water_req = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
        total_opponent_water_req += opp['water_requirement']

    total_demand = total_opponent_water_req + WATER_REQ

    # Base bid: a moderate fraction of daily salary
    base_bid = DAILY_SALARY * 0.55

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If opponents were bidding very high yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If my HP is good and supply is relatively abundant, I can risk bidding lower to save budget.
            if my_status['hp'] > 5 and current_supply >= total_demand:
                base_bid = DAILY_SALARY * 0.4
            else:
                # HP not good enough, or supply is tight, so I must compete aggressively.
                base_bid = DAILY_SALARY * 0.9
        else:
            # Opponents were bidding moderately or low. Try to slightly outbid the highest previous bid.
            base_bid = max(base_bid, highest_prev_bid + 2.0)

    # Adjust bid based on current supply vs. demand
    if current_supply < total_demand:
        # Supply is scarce, increase bid to secure water
        base_bid *= 1.15
    elif current_supply >= total_demand + WATER_REQ:
        # Supply is abundant, can try to bid lower
        base_bid *= 0.85

    # --- Budget and Long-term Survival Considerations ---
    # Estimate average cost per day to survive
    estimated_daily_cost = DAILY_SALARY * 0.6 # A conservative estimate
    remaining_days = EPISODE_DAYS - current_day
    
    # Ensure I have enough budget for remaining days, if possible
    if remaining_days > 0:
        required_budget_for_survival = estimated_daily_cost * remaining_days
        if my_status['budget'] < required_budget_for_survival * 1.2: # Budget getting tight
            if my_status['hp'] > 4: # If HP is still okay, try to conserve
                base_bid = min(base_bid, DAILY_SALARY * 0.5)
            elif my_status['hp'] <= 4: # HP low and budget tight, might be desperate for survival
                base_bid = max(base_bid, DAILY_SALARY * 0.8) # Bid higher to get water

    # Ensure bid does not exceed current budget and is at least 1
    final_bid = min(my_status['budget'], base_bid)
    final_bid = max(final_bid, 1.0)

    return final_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Identify strong opponents from context (Alex, David)
    strong_opponent_ids = ["Alex", "David"]
    active_strong_opponents = [o for o_id, o in opponents_status.items() if o['alive'] and o_id in strong_opponent_ids]

    # If no opponents, bid minimally
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Base bid calculation
    base_bid = DAILY_SALARY * 0.6 # Start with a moderate bid

    # Adjust based on my HP
    if my_status['hp'] <= 2: # Critical HP, must get water
        base_bid = DAILY_SALARY * 1.05 # Bid above salary
    elif my_status['hp'] <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.9
    elif my_status['hp'] >= 8: # High HP, can be more conservative
        base_bid = DAILY_SALARY * 0.4
    
    # Adjust based on day (later days, competition might intensify or budgets might dwindle)
    if day_context['day'] >= EPISODE_DAYS - 2: # Last few days
        base_bid = max(base_bid, DAILY_SALARY * 0.8) # Ensure survival

    # Analyze strong opponent's previous bids
    strong_opp_yesterday_bids = []
    for opp in active_strong_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            strong_opp_yesterday_bids.append(prev['bid'])

    if strong_opp_yesterday_bids:
        highest_strong_opp_bid = max(strong_opp_yesterday_bids)
        
        # If strong opponents bid high, I need to react
        if highest_strong_opp_bid >= DAILY_SALARY * 0.8: # They are bidding aggressively
            if my_status['hp'] <= 4: # I need water badly
                base_bid = max(base_bid, highest_strong_opp_bid + 5) # Try to outbid
            else: # I have some HP buffer
                base_bid = max(base_bid, highest_strong_opp_bid + 1) # Just slightly higher to compete
        elif highest_strong_opp_bid >= DAILY_SALARY * 0.5: # Moderately aggressive
            base_bid = max(base_bid, highest_strong_opp_bid * 0.95) # Try to get it slightly cheaper but still competitive
    else: # No strong opponent bids from yesterday (e.g., day 1 or they died)
        # If strong opponents are alive but no trace, assume they are competitive
        if active_strong_opponents:
            base_bid = max(base_bid, DAILY_SALARY * 0.7) # Assume moderate aggression

    # Consider supply scarcity
    # Water requirement for me is 13.
    # Total water needed for all alive players (including me) to get their full req.
    total_req_for_all_alive = (len(alive_opponents) + 1) * WATER_REQ
    
    # Is supply significantly less than total requirement?
    if day_context['supply'] < total_req_for_all_alive * 0.75: # Very scarce
        base_bid *= 1.15
        if my_status['hp'] <= 3:
            base_bid = max(base_bid, DAILY_SALARY * 1.1) # Bid very high if critical and scarce
    elif day_context['supply'] < total_req_for_all_alive: # Scarce
        base_bid *= 1.05

    # Ensure bid is not negative and within budget
    final_bid = max(1.0, base_bid)
    final_bid = min(final_bid, my_status['budget'])

    # If budget is critically low and HP is also low, bid all remaining budget
    if my_status['budget'] < DAILY_SALARY * 0.7 and my_status['hp'] <= 3:
        final_bid = my_status['budget']

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    my_current_hp = my_status['hp']
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']
    remaining_days = EPISODE_DAYS - current_day

    # Base bid - a moderate default
    bid_amount = DAILY_SALARY * 0.5

    # Aggressive bidding if HP is critical or missed water recently
    if my_current_hp <= 2 or my_no_water_days > 0:
        bid_amount = DAILY_SALARY * 0.95
    elif my_current_hp <= 4: # Low HP, need to be strong
        bid_amount = DAILY_SALARY * 0.8

    # Adjust bid based on perceived competition and supply
    # Estimate total water needed by all active players (including self)
    total_water_needed = WATER_REQ * (num_alive_opponents + 1)

    if day_context['supply'] < total_water_needed: # High competition scenario (not enough water for everyone)
        if my_current_hp <= 5: # Need water more desperately
            bid_amount = max(bid_amount, highest_prev_bid + DAILY_SALARY * 0.15) # Try to outbid significantly
            bid_amount = min(bid_amount, DAILY_SALARY * 0.99) # Cap it
        else: # Good HP, but still tight supply, need to be competitive
            bid_amount = max(bid_amount, highest_prev_bid + DAILY_SALARY * 0.05) # Slightly outbid
            bid_amount = min(bid_amount, DAILY_SALARY * 0.85) # Cap it
    else: # Sufficient supply, less competition
        if my_current_hp <= 3: # Still needs water, but can be slightly less aggressive
            bid_amount = max(bid_amount, highest_prev_bid + DAILY_SALARY * 0.05)
            bid_amount = min(bid_amount, DAILY_SALARY * 0.9)
        else: # Good HP, can try to get water cheaper
            bid_amount = max(DAILY_SALARY * 0.4, highest_prev_bid * 0.95) # Try to win with lower bid
            bid_amount = min(bid_amount, DAILY_SALARY * 0.7)
            if highest_prev_bid == 0: # If no one bid yesterday or all bid 0, set a reasonable default
                bid_amount = DAILY_SALARY * 0.4

    # Ensure bid is at least a minimal amount to be competitive, if I need water
    # Check if current HP is enough to survive the remaining days without any more water
    if my_current_hp < WATER_REQ * (remaining_days + 1): 
        bid_amount = max(bid_amount, DAILY_SALARY * 0.1)
    else: # I have enough HP to survive without water for the rest of the game
        bid_amount = 0 # No need to bid

    # Special handling for the last day
    if remaining_days == 0:
        if my_current_hp < WATER_REQ: # Need water to survive the last day
            bid_amount = min(my_status['budget'], DAILY_SALARY * 0.99)
        else: # Already have enough HP to survive last day
            bid_amount = 0

    # Cap bid by budget
    bid_amount = min(bid_amount, my_status['budget'])

    # Ensure bid is non-negative
    bid_amount = max(0.0, bid_amount)

    return bid_amount
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    TOTAL_DAYS = 10 # From episode_days

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Strategy 1: Survival mode if HP is low
    if my_status['hp'] <= 3:
        # Bid aggressively to survive, but don't overspend budget
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # Strategy 2: No competition, bid minimally
    if not alive_opponents:
        return min(my_status['budget'], 1.0) # Bid 1.0 to ensure winning water

    # Strategy 3: General competitive bidding
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid: a fraction of daily salary
    base_bid = DAILY_SALARY * 0.5

    # Adjust bid based on supply scarcity (higher bid for lower supply)
    # supply_pressure ranges from 0 (max supply) to 1 (min supply)
    supply_pressure = (MAX_SUPPLY - day_context['supply']) / (MAX_SUPPLY - MIN_SUPPLY)
    # Increase bid by up to 25% if supply is at its minimum
    supply_adjusted_bid = base_bid * (1 + supply_pressure * 0.25)

    current_bid = supply_adjusted_bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents bid very high, we need to be competitive
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Very aggressive
            current_bid = max(current_bid, highest_prev_bid + 2.0) # Try to outbid by a small margin
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # Moderately aggressive
            current_bid = max(current_bid, highest_prev_bid + 1.0) # Slightly outbid
        else: # Lower bids
            current_bid = max(current_bid, highest_prev_bid + 0.5) # Just barely outbid

    # Ensure bid is at least a minimum competitive level
    min_competitive_bid = DAILY_SALARY * 0.2
    current_bid = max(current_bid, min_competitive_bid)

    # Consider remaining days and budget
    remaining_days = TOTAL_DAYS - day_context['day'] + 1 # +1 because day_context['day'] is 1-indexed

    # If budget is tight relative to remaining days, be cautious
    # This condition checks if current budget is less than 70% of what's needed for remaining days assuming average daily spend
    if my_status['budget'] < (DAILY_SALARY * 0.7) * remaining_days:
        current_bid = min(current_bid, DAILY_SALARY * 0.75) # Cap bid to conserve budget, unless desperate (handled by HP check)

    # Final check: do not bid more than current budget
    current_bid = min(current_bid, my_status['budget'])

    # Also, usually don't bid more than daily salary significantly unless very desperate (handled by HP check)
    if my_status['hp'] > 5: # Not too desperate
        current_bid = min(current_bid, DAILY_SALARY * 1.05) # Max 5% over salary
    else: # Getting desperate but not critical (hp 4-5)
        current_bid = min(current_bid, DAILY_SALARY * 1.15) # Max 15% over salary

    return current_bid
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

    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    base_bid = DAILY_SALARY * 0.75

    # Emergency bid if HP is critical or missed water for multiple days
    if my_hp <= 3 or my_no_water_days >= 2:
        bid = min(my_budget, DAILY_SALARY * 1.05) # Bid slightly above salary to ensure win
        return max(1.0, bid)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # Opponents are very aggressive
            if my_hp > 5: # If HP is still good, be competitive but not reckless
                bid = max(base_bid, highest_prev_bid + 5)
            else: # My HP is getting lower, need water more
                bid = max(base_bid, highest_prev_bid + 10)
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            # Opponents are competitive
            bid = max(base_bid * 0.9, highest_prev_bid + 2)
        else:
            # Opponents were bidding low, try to save budget
            bid = max(base_bid * 0.7, highest_prev_bid + 1)
    else:
        # No previous bids from alive opponents, or all were 0. Stick to base.
        bid = base_bid

    # Water is always scarce for my requirement (13 units) given supply range (15-25).
    # Supply / WATER_REQ will always be 1, meaning less than 2 full requirements available.
    # So, competition is always high for full water. Increase bid.
    bid *= 1.1
    
    # Late game aggression if budget allows and HP is not perfect
    if current_day > EPISODE_DAYS / 2 and my_budget > DAILY_SALARY * 2:
        if my_hp < 7:
            bid *= 1.15

    bid = min(my_budget, bid)
    bid = max(1.0, bid) # Ensure bid is at least 1 to participate

    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid just enough to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine highest previous bid to react to
    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Define thresholds for bidding based on HP and opponent behavior
    CRITICAL_HP_THRESHOLD = 3
    HIGH_BID_THRESHOLD = DAILY_SALARY * 0.85 # 127.5
    LOW_BID_SAVE_BUDGET = DAILY_SALARY * 0.3 # 45
    DESPERATE_BID = DAILY_SALARY * 0.95 # 142.5
    MODERATE_BASE_BID = DAILY_SALARY * 0.5 # 75

    # Strategy based on highest previous bid and my HP
    if highest_prev_bid >= HIGH_BID_THRESHOLD:
        # Opponent bid very high yesterday.
        if my_status['hp'] > CRITICAL_HP_THRESHOLD:
            # I'm not desperate, let them win this round to save budget.
            return min(my_status['budget'], LOW_BID_SAVE_BUDGET)
        else:
            # I'm desperate, must get water, bid aggressively.
            return min(my_status['budget'], DESPERATE_BID)
    else:
        # Opponents' previous bids were not excessively high.
        if my_status['hp'] <= CRITICAL_HP_THRESHOLD:
            # I'm desperate, bid high to secure water.
            return min(my_status['budget'], DESPERATE_BID)
        else:
            # Not desperate, bid strategically above the highest previous bid,
            # but ensure it's at least a moderate amount.
            # Add a small increment to ensure winning against a tie.
            return min(my_status['budget'], max(MODERATE_BASE_BID, highest_prev_bid + 1.5))
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
    num_alive_players = len(alive_opponents) + 1

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    total_water_needed_by_all_players = num_alive_players * WATER_REQ
    current_bid = DAILY_SALARY * 0.5

    if day_context['supply'] < total_water_needed_by_all_players:
        if highest_prev_bid > 0:
            current_bid = max(current_bid, highest_prev_bid + (DAILY_SALARY * 0.05))
            if day_context['supply'] < total_water_needed_by_all_players * 0.7:
                 current_bid = max(current_bid, highest_prev_bid + (DAILY_SALARY * 0.1))
        else:
            current_bid = max(current_bid, DAILY_SALARY * 0.7)
    else:
        if my_status['hp'] > 5 and highest_prev_bid < DAILY_SALARY * 0.6:
            current_bid = DAILY_SALARY * 0.4
        elif highest_prev_bid > 0:
            current_bid = max(current_bid, highest_prev_bid * 0.9)
        else:
            current_bid = DAILY_SALARY * 0.45

    if highest_prev_bid > DAILY_SALARY * 0.8 and my_status['hp'] <= 5:
        current_bid = max(current_bid, highest_prev_bid + (DAILY_SALARY * 0.05))

    if day_context['day'] >= EPISODE_DAYS - 2 and my_status['hp'] <= 3:
        current_bid = max(current_bid, DAILY_SALARY * 0.9)

    final_bid = min(my_status['budget'], current_bid)
    final_bid = max(final_bid, DAILY_SALARY * 0.2)

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
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid a minimal amount to secure water
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid
    current_bid = DAILY_SALARY * 0.5 # Starting point

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        # If opponents bid high yesterday, react by increasing my bid
        if max_yesterday_bid >= DAILY_SALARY * 0.8: # Very high competition
            if my_status['hp'] > 5: # My HP is good, can be slightly conservative or competitive
                current_bid = max(current_bid, max_yesterday_bid * 0.9) # Slightly less than max, hoping they overbid
            else: # My HP is low, need to be aggressive
                current_bid = DAILY_SALARY * 0.95
        else: # Moderate competition
            current_bid = max(current_bid, max_yesterday_bid + 5.0) # Slightly outbid

    # Additional adjustments based on my status
    if my_status['hp'] <= 3: # Critical HP
        current_bid = DAILY_SALARY * 0.95
    elif my_status['no_water_days'] > 0: # Missed water yesterday
        current_bid = DAILY_SALARY * 0.85
    elif my_status['hp'] <= 5: # Low HP
        current_bid = DAILY_SALARY * 0.75

    # Adjust for supply scarcity
    available_slots = int(day_context['supply'] // WATER_REQ)
    if available_slots < num_alive_opponents + 1: # Not enough water for everyone
        if available_slots == 1 and num_alive_opponents >= 1: # Only one slot, high competition
            current_bid = max(current_bid, DAILY_SALARY * 0.9) # Bid very high
        else:
            current_bid = max(current_bid, DAILY_SALARY * 0.7) # Increase bid for scarcity

    # Adjust for end of game
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days
        if my_status['hp'] < 10 and my_status['budget'] > DAILY_SALARY: # Need water, have budget
            current_bid = max(current_bid, DAILY_SALARY * 0.9)

    # Ensure bid does not exceed budget
    current_bid = min(my_status['budget'], current_bid)

    # Ensure a minimal bid if budget allows and current bid is too low (e.g., 0)
    if current_bid < DAILY_SALARY * 0.05 and my_status['budget'] >= DAILY_SALARY * 0.05:
        current_bid = min(my_status['budget'], DAILY_SALARY * 0.05)
    elif current_bid <= 0.0 and my_status['budget'] > 0: # If bid somehow became 0 or negative, and budget allows
        current_bid = min(my_status['budget'], 1.0) # Bid a token amount

    return current_bid
"""
