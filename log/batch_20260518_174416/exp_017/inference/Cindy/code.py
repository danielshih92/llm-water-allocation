# ============================================================
# Experiment: exp_017
# Agent: Cindy
# Source: exp_017
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    # Bidding strategy constants derived from the example and my profile
    # The example uses hp > 3 for saving, and hp <= 2 for high bid.
    # This implies hp=3 is a neutral/moderate state.
    HP_THRESHOLD_FOR_SAVING_IN_HIGH_COMPETITION = 3 
    HP_THRESHOLD_FOR_DESPERATE_BID_OVERRIDE = 2 # This is the critical HP from example

    HIGH_COMPETITION_BID_THRESHOLD_PERCENT = 0.85
    
    BID_PERCENT_IF_ALONE = 0.4
    BID_PERCENT_IF_DESPERATE = 0.95 # Corresponds to example's 0.95
    BID_PERCENT_IF_SAVING = 0.3    # Corresponds to example's 0.3
    BID_PERCENT_DEFAULT = 0.55     # Corresponds to example's 0.55
    BID_INCREMENT_OVER_OPPONENT = 1.5 # Corresponds to example's 1.5

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid a low amount to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * BID_PERCENT_IF_ALONE)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_bid = 0.0 # Initialize bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # Scenario 1: Opponents were bidding very high yesterday (high competition)
        if highest_prev_bid >= DAILY_SALARY * HIGH_COMPETITION_BID_THRESHOLD_PERCENT:
            if my_status['hp'] > HP_THRESHOLD_FOR_SAVING_IN_HIGH_COMPETITION:
                # I'm not desperate (HP > 3), try to save money even if competition is high.
                current_bid = DAILY_SALARY * BID_PERCENT_IF_SAVING
            else:
                # I am desperate (HP <= 3), and competition is high. Bid very high.
                current_bid = DAILY_SALARY * BID_PERCENT_IF_DESPERATE
        else:
            # Scenario 2: Opponents were not extremely competitive yesterday.
            # Bid slightly above the highest previous bid to win, but ensure it's at least a default amount.
            current_bid = max(DAILY_SALARY * BID_PERCENT_DEFAULT, highest_prev_bid + BID_INCREMENT_OVER_OPPONENT)
    else:
        # Scenario 3: No yesterday bids available (e.g., first day or no valid traces).
        # Fallback to a default bid, which will be overridden by the HP check below if desperate.
        current_bid = DAILY_SALARY * BID_PERCENT_DEFAULT

    # Override for critical HP, similar to example's structure
    if my_status['hp'] <= HP_THRESHOLD_FOR_DESPERATE_BID_OVERRIDE: # If HP is 2 or 1
        current_bid = DAILY_SALARY * BID_PERCENT_IF_DESPERATE
    
    # Safeguard: if for some unexpected reason current_bid is still 0, set a default.
    if current_bid == 0.0:
        current_bid = DAILY_SALARY * BID_PERCENT_DEFAULT

    # Ensure bid does not exceed available budget
    return min(my_status['budget'], current_bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
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
    total_competitors = num_alive_opponents + 1 # Myself included

    # Scenario 1: No opponents left
    if num_alive_opponents == 0:
        # Bid minimum to get water at a nominal price
        return min(my_budget, WATER_REQ * 1.5)

    # Calculate available water units (slots)
    available_slots = int(current_supply // WATER_REQ)

    # Get yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid - a reasonable amount to secure water
    base_bid_percentage = 0.4 # Default to 40% of daily salary
    bid = DAILY_SALARY * base_bid_percentage

    # Adjust bid based on competitive pressure and supply
    if available_slots < total_competitors:
        # Supply is scarce, competition is high
        if my_hp <= 2 or my_no_water_days > 0:
            # Critical HP or missed water yesterday, must win
            bid = DAILY_SALARY * 0.95 # Bid very high
        elif my_hp <= 4:
            # Low HP, need water
            bid = DAILY_SALARY * 0.8
        else:
            # Not critical, but competition is high
            bid = DAILY_SALARY * 0.65
        
        # Factor in highest previous bid if it was significant
        if highest_prev_bid > bid * 0.8: # If highest bid was significantly high
            bid = max(bid, highest_prev_bid + 5) # Bid slightly above the highest if competitive
        
    else:
        # Supply is abundant or sufficient
        if my_hp <= 2 or my_no_water_days > 0:
            # Critical HP, but supply is good, so can be slightly less aggressive
            bid = DAILY_SALARY * 0.7
        elif my_hp <= 4:
            bid = DAILY_SALARY * 0.55
        else:
            # Healthy HP, supply is good, can conserve budget
            bid = DAILY_SALARY * 0.35 # Conservative bid

        # If highest_prev_bid was still high even with abundant supply, respect it but try to undercut
        if highest_prev_bid > bid and available_slots < total_competitors * 1.5: # If supply isn't *super* abundant
             bid = max(bid, highest_prev_bid - 5) # Try to undercut slightly if possible, or match

    # Adjust for end game pressure
    days_left = EPISODE_DAYS - current_day
    if days_left <= 2: # Last 2 days
        if my_hp <= 3:
            bid = max(bid, DAILY_SALARY * 0.9) # Be very aggressive to survive
        else:
            bid = max(bid, DAILY_SALARY * 0.7) # Still aggressive but not maxed out

    # Ensure bid is at least enough to cover water_requirement at a minimal price
    min_survival_bid_per_unit = 1.0 
    min_survival_bid = WATER_REQ * min_survival_bid_per_unit
    bid = max(bid, min_survival_bid)

    # Ensure bid does not exceed current budget, and is not negative if budget allows.
    final_bid = min(my_budget, bid)
    
    # If budget is 0 or negative, bid 0.
    if my_budget <= 0:
        final_bid = 0

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

    # --- Determine base bid ---
    bid = DAILY_SALARY * 0.6 # A solid bid for survival

    # --- Adjust bid based on personal urgency (HP and no_water_days) ---
    if my_hp <= 2 or my_no_water_days > 0:
        # Critical state: Must get water. Bid very aggressively.
        bid = DAILY_SALARY * 0.95 # Almost full salary
    elif my_hp <= 5:
        # Low HP: Need water soon. Bid aggressively.
        bid = DAILY_SALARY * 0.8
    elif my_hp <= 7 and current_day > EPISODE_DAYS / 2:
        # Mid-game, slightly low HP, need to keep up
        bid = DAILY_SALARY * 0.75

    # --- Adjust bid based on perceived competition (David) ---
    david_bid_yesterday = 0.0
    david_is_alive = False
    for opp_id, opp_data in opponents_status.items():
        if opp_id == "David" and opp_data['alive']:
            david_is_alive = True
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                david_bid_yesterday = prev_trace['bid']
            break

    if david_is_alive and david_bid_yesterday > 0:
        # David is the main threat, he bids high. Try to outbid him.
        if david_bid_yesterday >= DAILY_SALARY * 0.6: # If David bid significantly
            # Ensure our bid is at least slightly higher than David's last high bid
            bid = max(bid, david_bid_yesterday + 5)
        else:
            # If David's bid was not that high, just ensure we are competitive
            bid = max(bid, david_bid_yesterday)

    # --- Adjust bid based on supply scarcity ---
    if current_supply <= WATER_REQ + 2: # Very tight supply
        bid *= 1.1 # Increase bid
    elif current_supply >= WATER_REQ + 10 and my_hp > 5: # Abundant supply and not critical
        bid *= 0.9 # Decrease bid to save budget

    # --- Late game push (if I have budget and am doing okay) ---
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_hp > 0 and my_budget > DAILY_SALARY * 1.5:
        # Last days, if I have budget and am not dead, go aggressive
        bid = max(bid, DAILY_SALARY * 1.2)

    # --- Final checks ---
    # Ensure bid doesn't exceed available budget
    final_bid = min(my_budget, bid)

    # Ensure bid is at least 1 to participate
    final_bid = max(1.0, final_bid)

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

    # If no opponents, bid low to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Decision logic based on yesterday's highest pressure
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # High pressure scenario: opponents were bidding high
        if highest_prev_bid >= DAILY_SALARY * 0.85: # 127.5
            if my_status['hp'] > 3:
                # Healthy, can risk bidding lower to save budget
                return min(my_status['budget'], DAILY_SALARY * 0.3) # 45
            # Low HP, need water, bid very high
            return min(my_status['budget'], DAILY_SALARY * 0.95) # 142.5
        
        # Moderate pressure scenario: opponents were not bidding excessively high
        # Be competitive, slightly above their highest previous bid, with a floor
        return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)) # Floor 75

    # General case (e.g., first day, or no previous bids from alive opponents)
    if my_status['hp'] <= 2:
        # Low HP, bid high to ensure survival
        return min(my_status['budget'], DAILY_SALARY * 0.9) # 135
    
    # Healthy HP, bid moderately
    return min(my_status['budget'], DAILY_SALARY * 0.55) # 82.5
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
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

    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.98)
    
    if my_status['hp'] <= 5:
        base_bid = DAILY_SALARY * 0.9
    else:
        base_bid = DAILY_SALARY * 0.7
        if highest_prev_bid > 0:
            if highest_prev_bid > DAILY_SALARY * 0.8:
                 base_bid = max(base_bid, highest_prev_bid + 1)
                 base_bid = min(base_bid, DAILY_SALARY * 0.95)
            else:
                base_bid = max(base_bid, highest_prev_bid * 1.05)
                base_bid = min(base_bid, DAILY_SALARY * 0.8)
        
    normalized_supply = (day_context['supply'] - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    scarcity_factor = 1 - normalized_supply
    supply_adjustment = scarcity_factor * (DAILY_SALARY * 0.1)
    final_bid = base_bid + supply_adjustment

    normalized_day = day_context['day'] / EPISODE_DAYS
    day_adjustment = normalized_day * (DAILY_SALARY * 0.1)
    final_bid = final_bid + day_adjustment

    final_bid = min(my_status['budget'], final_bid, DAILY_SALARY * 0.99)
    
    final_bid = max(final_bid, 1.0)

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        # If no opponents, bid minimally to get water (e.g., 1 credit per unit)
        return min(my_status['budget'], WATER_REQ * 1.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    bid = 0.0
    current_supply = day_context['supply']
    
    # Calculate total water needed if everyone alive wants their requirement
    total_water_needed_by_all = WATER_REQ * (num_alive_opponents + 1) # Including myself

    # Critical HP or recently had no water: Must get water at almost any cost
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        bid = DAILY_SALARY * 0.95
        if highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid * 1.15) # Bid significantly higher than the highest opponent
    # Low HP: Need water urgently
    elif my_status['hp'] <= 5:
        bid = DAILY_SALARY * 0.75
        if highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid + 15) # Outbid by a fixed margin
    # Healthy HP: Can be more strategic
    else:
        if current_supply < total_water_needed_by_all: # Supply is scarce for everyone
            bid = DAILY_SALARY * 0.6
            if highest_prev_bid > 0:
                bid = max(bid, highest_prev_bid + 8) # Be aggressive but not desperate
        else: # Supply is ample, can be more conservative
            bid = DAILY_SALARY * 0.4
            if highest_prev_bid > 0:
                bid = max(bid, highest_prev_bid + 2) # Just slightly above to win if possible
            else:
                bid = max(bid, DAILY_SALARY * 0.3) # Default conservative bid if no previous bids

    # Ensure bid is always positive and within budget
    bid = min(my_status['budget'], bid)
    bid = max(bid, 1.0) # Minimum bid to participate

    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Default aggressive bid due to constant extreme scarcity (only one agent can get full water)
    default_bid = DAILY_SALARY * 0.8 # 120

    # If I'm the only one left, bid minimally
    if num_alive_opponents == 0:
        return max(1.0, min(my_status['budget'], DAILY_SALARY * 0.3))

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    my_current_bid = default_bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If my HP is critically low, I must win at almost any cost
        if my_status['hp'] <= 2:
            my_current_bid = DAILY_SALARY * 0.95 # 142.5
        # If my HP is moderately low, be very competitive
        elif my_status['hp'] <= 4:
            my_current_bid = max(highest_prev_bid + 5.0, DAILY_SALARY * 0.9) # 135
        # If my HP is healthy
        else:
            # If opponents were very aggressive yesterday, stay competitive
            if highest_prev_bid >= DAILY_SALARY * 0.85: # 127.5
                my_current_bid = max(highest_prev_bid + 2.0, DAILY_SALARY * 0.8) # 120
            # If opponents were less aggressive, bid slightly above them to win efficiently
            else:
                my_current_bid = max(highest_prev_bid + 2.0, DAILY_SALARY * 0.75) # 112.5
    else: # No yesterday bids (e.g., Day 1 of a new meta-round with opponents)
        if my_status['hp'] <= 2:
            my_current_bid = DAILY_SALARY * 0.9 # 135 - desperate
        elif my_status['hp'] <= 4:
            my_current_bid = DAILY_SALARY * 0.85 # 127.5
        else:
            my_current_bid = DAILY_SALARY * 0.8 # 120 - default aggressive bid

    # Ensure bid does not exceed budget and is at least 1.0
    final_bid = min(my_status['budget'], my_current_bid)
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If I'm the only one alive, bid minimum to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid initialization
    target_bid = DAILY_SALARY * 0.55 # Default moderate bid
    
    # Adjust target_bid based on my HP
    if my_status['hp'] <= 2:
        target_bid = DAILY_SALARY * 0.95 # Critically low HP, bid very high
    elif my_status['hp'] <= 4:
        target_bid = DAILY_SALARY * 0.8 # Low HP, bid high
    
    # Adjust target_bid based on previous bids if available
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if my_status['hp'] <= 4: # Low or critical HP, prioritize winning against previous bids
            target_bid = max(target_bid, highest_prev_bid + 5) # Ensure outbidding
        else: # Healthy HP, be competitive but try to save
            if highest_prev_bid >= DAILY_SALARY * 0.8: # Previous bid was very high
                target_bid = max(target_bid, highest_prev_bid + 1) # Just barely outbid
            else: # Previous bid was moderate
                target_bid = max(target_bid, highest_prev_bid + 2.5) # A bit more buffer

    # Final adjustment based on remaining days (late game aggressiveness)
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 3 and my_status['hp'] <= 6: # Late game, not perfectly healthy, increase bid
        target_bid = max(target_bid, DAILY_SALARY * 0.75) # Ensure a strong bid
    elif remaining_days <= 2 and my_status['hp'] > 6: # Very late game, healthy, still be competitive
        target_bid = max(target_bid, DAILY_SALARY * 0.6)

    # Ensure bid doesn't exceed budget
    return min(my_status['budget'], target_bid)
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid low to save money, but ensure water
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    max_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    # Calculate total water needed for all alive players + self
    total_water_needed = WATER_REQ # My requirement
    for opp in alive_opponents:
        total_water_needed += opp['water_requirement']

    # Determine bidding strategy based on HP and supply/competition

    # Aggressive bidding if HP is very low (e.g., 1 day left)
    if my_status['hp'] <= 1:
        # Bid high to ensure survival, capped by daily salary
        return min(my_status['budget'], DAILY_SALARY, DAILY_SALARY * 0.95)
    
    # Moderate aggressive if HP is low (e.g., 2-3 days left)
    if my_status['hp'] <= 3:
        # If supply is very tight or competition was high yesterday
        if current_supply < total_water_needed or max_yesterday_bid > DAILY_SALARY * 0.7:
            return min(my_status['budget'], DAILY_SALARY, DAILY_SALARY * 0.8)
        else:
            # Still bid relatively high, but not max, capped by daily salary
            return min(my_status['budget'], DAILY_SALARY, DAILY_SALARY * 0.7)

    # If HP is good (more than 3 days)
    # Check for supply abundance
    if current_supply >= total_water_needed: # Supply is enough for everyone to get their required water
        # If yesterday's bids were high, we can try to undercut slightly or match, capped by daily salary
        if max_yesterday_bid > DAILY_SALARY * 0.5:
            return min(my_status['budget'], DAILY_SALARY, max(DAILY_SALARY * 0.4, max_yesterday_bid * 0.9))
        else:
            # Low competition, ample supply, bid low to save, capped by daily salary
            return min(my_status['budget'], DAILY_SALARY, DAILY_SALARY * 0.3)
    else: # Supply is tight, not enough for everyone to get their required water
        # If yesterday's bids were high, we need to be competitive, capped by daily salary
        if max_yesterday_bid > DAILY_SALARY * 0.6:
            # Bid slightly above the max yesterday bid to win, but not exceeding salary
            return min(my_status['budget'], DAILY_SALARY, max(DAILY_SALARY * 0.65, max_yesterday_bid + 5))
        else:
            # Competition not too high yesterday, but supply is tight, bid moderately, capped by daily salary
            return min(my_status['budget'], DAILY_SALARY, DAILY_SALARY * 0.6)

    # Fallback bid (should not be reached with current logic), capped by daily salary
    return min(my_status['budget'], DAILY_SALARY, DAILY_SALARY * 0.5)
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
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    yesterday_bids = []
    eric_prev_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            if opp['agent_id'] == 'Eric':
                eric_prev_bid = prev['bid']

    base_bid = DAILY_SALARY * 0.75

    if my_hp <= 3 or my_no_water_days > 0:
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 6:
        base_bid = DAILY_SALARY * 0.88

    if current_day >= EPISODE_DAYS - 2:
        base_bid = DAILY_SALARY * 0.99
    elif current_day >= EPISODE_DAYS - 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.92)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        high_threshold = DAILY_SALARY * 0.8

        if eric_prev_bid > high_threshold:
            base_bid = max(base_bid, eric_prev_bid + 2.0)
        elif highest_prev_bid > high_threshold:
            if my_hp > 5 and current_day < EPISODE_DAYS - 3:
                base_bid = max(base_bid, highest_prev_bid + 1.0)
            else:
                base_bid = max(base_bid, highest_prev_bid + 2.0)
        else:
            if my_hp > 5 and current_day < EPISODE_DAYS - 3:
                base_bid = min(base_bid, highest_prev_bid + 5.0)
            else:
                base_bid = max(base_bid, highest_prev_bid + 10.0)

    final_bid = min(my_budget, base_bid)
    return max(1.0, final_bid)
"""
