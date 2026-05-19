# ============================================================
# Experiment: exp_025
# Agent: Cindy
# Source: exp_025
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    TOTAL_DAYS = 10

    # Constants for bidding thresholds
    MINIMAL_BID = 1.0 # Smallest positive bid
    LOW_BID_PERCENTAGE = 0.2
    MEDIUM_BID_PERCENTAGE = 0.5
    HIGH_BID_PERCENTAGE = 0.8
    CRITICAL_BID_PERCENTAGE = 0.95

    low_bid_val = DAILY_SALARY * LOW_BID_PERCENTAGE
    medium_bid_val = DAILY_SALARY * MEDIUM_BID_PERCENTAGE
    high_bid_val = DAILY_SALARY * HIGH_BID_PERCENTAGE
    critical_bid_val = DAILY_SALARY * CRITICAL_BID_PERCENTAGE

    # Identify alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Determine available water slots
    current_supply = day_context['supply']
    # CRITICAL INDEX RULE: supply is float, so int() for division result if used as index
    num_water_slots = int(current_supply // WATER_REQ)

    # Strategy 1: No active opponents - bid minimal to save budget
    if num_alive_opponents == 0:
        # If I am the only one, bid just enough to secure water
        return min(my_status['budget'], max(MINIMAL_BID, low_bid_val * 0.5))

    # Strategy 2: High personal urgency (low HP or consecutive no-water days)
    # Prioritize survival
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        return min(my_status['budget'], critical_bid_val)

    # Strategy 3: Analyze yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid based on competition and yesterday's activity
    current_bid = medium_bid_val # Default bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If competition was fierce yesterday or expected to be fierce today
        if num_alive_opponents >= num_water_slots:
            # Bid higher than yesterday's highest, but capped by high_bid_val
            current_bid = max(highest_prev_bid + 5, high_bid_val)
        else:
            # Competition was less fierce, try to outbid slightly
            current_bid = max(highest_prev_bid + 2, medium_bid_val)
    else:
        # No previous bids (e.g., Day 1 or opponents didn't bid/died)
        # Base bid on current competition level
        if num_alive_opponents >= num_water_slots:
            current_bid = high_bid_val
        else:
            current_bid = medium_bid_val

    # Ensure bid is positive and within budget
    final_bid = min(my_status['budget'], max(MINIMAL_BID, current_bid))

    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to save budget.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Default base bid
    calculated_bid = DAILY_SALARY * 0.6

    # Survival mode: If HP is low (2 or less) or no_water_days is increasing (1 or more)
    # This takes precedence over other bidding strategies.
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        # Bid very aggressively to survive.
        # If it's the last few days, be even more aggressive.
        if day_context['day'] >= EPISODE_DAYS - 1: # Last 2 days (Day 9 or 10)
            return min(my_status['budget'], DAILY_SALARY * 1.1) # Bid above salary if necessary
        return min(my_status['budget'], DAILY_SALARY * 0.95) # High bid for survival

    # React to opponents' previous bids if available
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents bid high yesterday (e.g., above 80% of daily salary)
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            # If supply is tight, bid slightly above to secure water.
            if day_context['supply'] <= MIN_SUPPLY + 5: # e.g., supply <= 20
                calculated_bid = highest_prev_bid + (DAILY_SALARY * 0.05) # Bid slightly higher
            else: # Supply is more abundant, try to be competitive but not overspend.
                calculated_bid = max(calculated_bid, highest_prev_bid * 0.95) # Try to match or slightly undercut
        # If opponents bid moderately or low yesterday
        else:
            calculated_bid = max(calculated_bid, highest_prev_bid + (DAILY_SALARY * 0.02)) # Bid slightly above to secure
    
    # Further adjust based on current supply conditions
    # If supply is very abundant, try to get it cheaper.
    if day_context['supply'] >= MAX_SUPPLY - 3: # e.g., supply >= 22
        calculated_bid = min(calculated_bid, DAILY_SALARY * 0.5)
    # If supply is very scarce, increase bid to compete.
    elif day_context['supply'] <= MIN_SUPPLY + 3: # e.g., supply <= 18
        calculated_bid = max(calculated_bid, DAILY_SALARY * 0.8)

    # Ensure the bid is within budget and at least a minimal amount if budget allows
    final_bid = max(1.0, min(my_status['budget'], calculated_bid))
    
    # Prevent bidding 0 if budget is available
    if final_bid == 0 and my_status['budget'] > 0:
        final_bid = 1.0

    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.15)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.5

    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] <= 7:
        base_bid = DAILY_SALARY * 0.65
    else:
        base_bid = DAILY_SALARY * 0.5

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] <= 4:
                base_bid = max(base_bid, highest_prev_bid + 5)
            else:
                base_bid = max(base_bid, highest_prev_bid * 0.9)
        
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            base_bid = max(base_bid, highest_prev_bid + 2)
        
        else:
            base_bid = max(base_bid, highest_prev_bid + 1)

    final_bid = min(my_status['budget'], base_bid)

    if final_bid < DAILY_SALARY * 0.1 and my_status['hp'] < 10:
        final_bid = max(final_bid, DAILY_SALARY * 0.15)

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

    if not alive_opponents:
        # No opponents, bid minimally to save budget
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # 1. Determine a base bid based on my daily salary
    base_bid = DAILY_SALARY * 0.5 # Start with 75

    # 2. Adjust base bid based on supply scarcity
    # supply_factor is 0 when supply is MAX_SUPPLY, and 1 when supply is MIN_SUPPLY
    supply_factor = (MAX_SUPPLY - day_context['supply']) / (MAX_SUPPLY - MIN_SUPPLY)
    # Increase bid by up to 30% of base_bid if supply is very scarce
    base_bid *= (1 + supply_factor * 0.3)

    my_current_bid = base_bid

    # 3. Adjust bid based on my HP (prioritize survival)
    if my_status['hp'] <= 2: # Critical HP
        my_current_bid = DAILY_SALARY * 0.95 # Bid very high to survive
    elif my_status['hp'] <= 4: # Low HP
        my_current_bid = max(my_current_bid, DAILY_SALARY * 0.75) # Ensure a higher bid
    elif my_status['hp'] <= 6: # Medium HP
        my_current_bid = max(my_current_bid, DAILY_SALARY * 0.6) # Ensure a decent bid

    # 4. Adjust based on opponents' previous highest bid from yesterday's trace
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest bid was aggressive, consider bidding slightly above it
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Very aggressive last round by an opponent
            my_current_bid = max(my_current_bid, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # Moderately aggressive
            my_current_bid = max(my_current_bid, highest_prev_bid + 2)
        else: # Opponents bid relatively low
            # If my HP is good, I can try to save money but still aim to win
            if my_status['hp'] > 6: 
                my_current_bid = max(my_current_bid, highest_prev_bid * 1.05 + 1) # Slightly above their low bid
            # If HP is not high, my HP-based bid already ensures a higher bid, so no need to lower it.

    # Ensure a minimum bid to stay in contention, especially if HP is not full
    # Assuming max HP is 10 for calculation if not explicitly given
    if my_status['hp'] < 10: 
        my_current_bid = max(my_current_bid, DAILY_SALARY * 0.2) # Minimum bid to stay in game
    else: # If HP is full, can afford to be more conservative
        my_current_bid = max(my_current_bid, DAILY_SALARY * 0.1)

    # Final check: Don't bid more than current budget
    my_current_bid = min(my_status['budget'], my_current_bid)
    
    # Ensure bid is positive
    my_current_bid = max(0.01, my_current_bid)

    return my_current_bid
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

    # If no active opponents or very early in the episode, bid moderately to secure water.
    # This also acts as a baseline if no previous bids are available.
    if not alive_opponents or day_context['day'] <= 2:
        # Consider supply: if high, try to get it cheaper, else be more firm.
        if day_context['supply'] >= WATER_REQ * 1.5: # Enough for one and a half requirements, implies less fierce competition
            return min(my_status['budget'], DAILY_SALARY * 0.4)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.6)


    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        # Ensure 'bid' key exists and is not None
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # If no previous bids from alive opponents (e.g., all previous died, new ones appeared, or day 1)
    if not yesterday_bids:
        if my_status['hp'] <= 3: # Desperate for water
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        return min(my_status['budget'], DAILY_SALARY * 0.55) # Default conservative bid

    highest_prev_bid = max(yesterday_bids)

    # Strategy based on highest previous bid and my HP, considering opponent's observed overbidding behavior.

    # If highest bid was very high, indicating strong competition (and potential overbidding by opponents)
    if highest_prev_bid >= DAILY_SALARY * 0.8: # e.g., bid >= 120
        if my_status['hp'] > 3: # My HP is good, can afford to be less aggressive to conserve budget and outlast opponents
            return min(my_status['budget'], DAILY_SALARY * 0.4) # Bid 60
        else: # My HP is low, must secure water aggressively
            return min(my_status['budget'], DAILY_SALARY * 0.95) # Bid 142.5

    # If highest bid was moderate, bid slightly above it to win, but don't overpay excessively.
    elif highest_prev_bid >= DAILY_SALARY * 0.5: # e.g., bid >= 75
        if my_status['hp'] > 2: # Good to moderate HP
            return min(my_status['budget'], max(DAILY_SALARY * 0.55, highest_prev_bid + 5)) # Bid at least 82.5 or prev+5
        else: # Low HP, need water, be more aggressive but still consider previous bids
            return min(my_status['budget'], max(DAILY_SALARY * 0.7, highest_prev_bid + 10)) # Bid at least 105 or prev+10

    # If highest bid was low, try to get water cheaply.
    else: # highest_prev_bid < DAILY_SALARY * 0.5 (less than 75)
        if my_status['hp'] > 2: # Good to moderate HP
            return min(my_status['budget'], max(DAILY_SALARY * 0.4, highest_prev_bid + 2)) # Bid at least 60 or prev+2
        else: # Low HP, secure water, but don't overpay if competition is weak
            return min(my_status['budget'], max(DAILY_SALARY * 0.6, highest_prev_bid + 5)) # Bid at least 90 or prev+5

    # Fallback to ensure a bid is always returned (should not be reached with comprehensive if/elif/else)
    return min(my_status['budget'], DAILY_SALARY * 0.5)
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

    # If no opponents are alive, bid a minimal amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Calculate days remaining in the episode
    days_remaining = EPISODE_DAYS - day_context['day'] + 1

    # Determine base bid aggressiveness based on current HP
    # Given the extreme competition (only one player gets full water), bids must be high.
    if my_status['hp'] <= 2:
        # Critical HP: Must get water at almost any cost
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5:
        # Low to medium HP: Need water soon, bid very high
        base_bid = DAILY_SALARY * 0.85
    else:
        # Good HP: Can afford to be slightly less aggressive, but still need to win
        base_bid = DAILY_SALARY * 0.75

    # Adjust bid based on opponent's previous day's bids
    highest_prev_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])

    # Ensure we outbid the highest previous bid from opponents, with a small margin
    # This is critical because only one player can get full water.
    calculated_bid = max(base_bid, highest_prev_bid + 5.0)

    # Increase aggressiveness towards the end of the episode
    if days_remaining <= 2:
        calculated_bid = max(calculated_bid, DAILY_SALARY * 0.98)
    elif days_remaining <= 4:
        calculated_bid = max(calculated_bid, DAILY_SALARY * 0.90)

    # Ensure the bid does not exceed available budget
    final_bid = min(my_status['budget'], calculated_bid)

    # If budget is extremely low and HP is critical, bid all remaining budget
    if my_status['budget'] < calculated_bid and my_status['hp'] <= 3:
        return my_status['budget']

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
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Default bid if no specific conditions met or no yesterday's bids
    bid_to_make = DAILY_SALARY * 0.55 # A moderate default bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.85: # High competition threshold (127.5 for Cindy)
            if my_status['hp'] > 3: # Not critical (HP > 3), can be slightly less aggressive to save
                # Bid enough to potentially win, but don't overspend if not desperate
                bid_to_make = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.0) # Ensure it's at least 0.5 * salary
                bid_to_make = min(bid_to_make, DAILY_SALARY * 0.8) # Cap if HP is good (max 120)
            else: # Critical HP (<=3), must win
                bid_to_make = max(DAILY_SALARY * 0.95, highest_prev_bid + 5.0) # Very aggressive (min 142.5)
        else: # Moderate competition (highest_prev_bid < 127.5)
            # Bid slightly above to secure water, ensuring it's at least a moderate default
            bid_to_make = max(DAILY_SALARY * 0.55, highest_prev_bid + 1.5)
    
    # If no yesterday_bids, or if the above logic didn't set a higher bid,
    # and HP is critical, override with a high bid to prioritize survival.
    if my_status['hp'] <= 2: # Very critical HP
        bid_to_make = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5 and bid_to_make < DAILY_SALARY * 0.8: # Low HP, ensure bid is at least 80% (120)
        bid_to_make = DAILY_SALARY * 0.8

    # Ensure bid is non-negative and within current budget
    return min(my_status['budget'], max(0.0, bid_to_make))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents are alive, bid conservatively to ensure survival
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine the highest bid from yesterday among active opponents
    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # --- Bidding Logic ---

    # 1. Survival Mode: If HP is critically low or I missed water yesterday
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        # Bid very aggressively to survive
        return float(min(my_status['budget'], DAILY_SALARY * 0.95))
    
    # 2. Late Game Aggression: If it's getting close to the end and I need water
    if day_context['day'] >= EPISODE_DAYS - 3: # Last 3 days
        # In late game, always bid high to secure water, especially if HP isn't perfect
        return float(min(my_status['budget'], DAILY_SALARY * 0.9))

    # 3. Normal Game: Adjust bid based on previous competition
    # Since my WATER_REQ is 13 and supply is 15-25, there's always effectively only 1 "slot" for me, making it competitive.

    # If the highest opponent bid yesterday was very high (Alex/Eric behavior)
    if highest_prev_bid >= DAILY_SALARY * 0.8: 
        if my_status['hp'] > 4: # If my HP is good, I can try to save budget
            # Bid moderately, but still enough to show intent, might lose but save budget
            bid = DAILY_SALARY * 0.5 
            strong_opp_bids = [b for b in yesterday_bids if b >= DAILY_SALARY * 0.7]
            if strong_opp_bids:
                bid = max(bid, max(strong_opp_bids) * 0.9) # Don't completely ignore strong opponents
            return float(min(my_status['budget'], bid))
        else: # HP is not great, need water, bid very high
            return float(min(my_status['budget'], DAILY_SALARY * 0.9))
    
    # If highest opponent bid was moderate or low
    # Try to win by bidding slightly above the highest previous bid, or a solid base
    bid = max(DAILY_SALARY * 0.55, highest_prev_bid + 2.0) 
    
    # Ensure bid is within budget and non-negative
    bid = min(my_status['budget'], bid)
    bid = max(0.0, bid)

    # Ensure a minimum bid if budget allows, to stay in the game
    if my_status['budget'] > 0 and bid < DAILY_SALARY * 0.1:
        bid = DAILY_SALARY * 0.1

    return float(bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no active opponents, bid a minimal amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Default bid if no previous bids are available (e.g., Day 1 or all opponents new)
    if not yesterday_bids:
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        return min(my_status['budget'], DAILY_SALARY * 0.55)

    highest_prev_bid = max(yesterday_bids)

    # Adjust bid based on opponent's previous aggression and my health
    if highest_prev_bid >= DAILY_SALARY * 0.85: # Opponent was very aggressive
        if my_status['hp'] > 3: # I am relatively healthy, can afford to be conservative
            bid = DAILY_SALARY * 0.3
        else: # I am not healthy, must bid aggressively to survive
            bid = DAILY_SALARY * 0.95
    else: # Opponent was not overly aggressive, try to win efficiently
        # Bid slightly above their highest previous bid, but no less than a base amount
        bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)

    # Ensure bid doesn't exceed current budget
    return min(my_status['budget'], bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    bid = DAILY_SALARY * 0.5

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], 1.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    if highest_prev_bid > 0:
        if my_status['hp'] > 5:
            bid = max(bid, highest_prev_bid + 5.0)
        else:
            bid = max(bid, highest_prev_bid + 10.0)
    else:
        if day_context['day'] == 1:
            bid = DAILY_SALARY * 0.6
        else:
            bid = DAILY_SALARY * 0.55

    if my_status['hp'] <= 3:
        bid = max(bid, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 5:
        bid = max(bid, DAILY_SALARY * 0.8)
    elif my_status['no_water_days'] > 0:
        bid = max(bid, DAILY_SALARY * 0.7)

    if day_context['day'] >= EPISODE_DAYS - 2:
        bid = max(bid, DAILY_SALARY * 0.9)

    bid = min(bid, my_status['budget'])

    bid = max(bid, 1.0)

    if my_status['hp'] > 3:
        bid = min(bid, DAILY_SALARY * 0.98)

    return bid
"""
