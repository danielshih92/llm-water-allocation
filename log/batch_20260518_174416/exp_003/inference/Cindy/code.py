# ============================================================
# Experiment: exp_003
# Agent: Cindy
# Source: exp_003
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
    total_active_players = num_alive_opponents + 1 # Include myself

    # --- Survival Bids ---
    # If HP is critical (2 or less) or I missed water yesterday, bid very high to survive.
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        return min(my_status['budget'], DAILY_SALARY * 0.98) # Very aggressive bid

    # --- No Opponents / Ample Supply ---
    if not alive_opponents:
        # No competition, bid low to conserve budget while securing water.
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    supply = day_context['supply']
    # Calculate how many players can get their full water requirement.
    num_possible_winners = int(supply // WATER_REQ)

    # If there's enough water for everyone to get their requirement, bid moderately.
    if num_possible_winners >= total_active_players:
        # Still bid moderately to ensure a win, but don't overspend unnecessarily.
        return min(my_status['budget'], DAILY_SALARY * 0.5)

    # --- Competitive Bidding based on Opponent's Previous Actions ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.6 # Default moderate competitive bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If opponents were very aggressive yesterday (bid high).
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If I have decent HP buffer, try to outbid them slightly.
            if my_status['hp'] > 4:
                base_bid = max(base_bid, highest_prev_bid + 2) 
            else:
                # Less buffer, need water more, so bid more aggressively.
                base_bid = max(base_bid, highest_prev_bid + 5) 
        # If opponents were conservative yesterday (bid low).
        elif highest_prev_bid < DAILY_SALARY * 0.5:
            # Even if opponents were conservative, if supply is tight, maintain a competitive bid.
            if num_possible_winners < total_active_players:
                base_bid = max(base_bid, DAILY_SALARY * 0.6) 
            else:
                base_bid = max(base_bid, DAILY_SALARY * 0.4) # More conservative if ample water
        else:
            # Moderate previous bids, react by slightly exceeding the highest previous bid to win.
            base_bid = max(base_bid, highest_prev_bid + 1)
    
    # If no previous bids (e.g., Day 1) and supply is tight, use a solid competitive bid.
    if not yesterday_bids and num_possible_winners < total_active_players:
        base_bid = DAILY_SALARY * 0.7 # Solid competitive bid for initial competitive scenarios

    # Ensure the bid does not exceed the current budget.
    return min(my_status['budget'], base_bid)
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

    # If no opponents or all are dead, bid minimally to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    my_hp = my_status['hp']
    current_supply = day_context['supply']

    # Base bid: Start with a moderate bid
    bid_amount = DAILY_SALARY * 0.5 # Default to 75

    # Strategy 1: Prioritize survival when HP is low
    if my_hp <= 2: # Critical HP
        bid_amount = DAILY_SALARY * 0.95 # 142.5
    elif my_hp <= 5: # Low HP
        bid_amount = DAILY_SALARY * 0.85 # 127.5
    elif my_hp <= 7: # Mid HP
        bid_amount = DAILY_SALARY * 0.7 # 105
    # If HP > 7, bid_amount remains DAILY_SALARY * 0.5 (75) initially

    # Strategy 2: React to opponent's previous highest bid
    # Always try to outbid max_yesterday_bid to secure water,
    # but be more aggressive if my HP is low.
    if max_yesterday_bid > 0:
        if my_hp <= 5: # Low HP, be very aggressive to win
            bid_amount = max(bid_amount, max_yesterday_bid + 15)
        elif my_hp <= 7: # Mid HP, be aggressive
            bid_amount = max(bid_amount, max_yesterday_bid + 10)
        else: # High HP, try to win but don't overpay too much
            bid_amount = max(bid_amount, max_yesterday_bid + 5)

    # Strategy 3: Adjust based on supply
    # If supply is tight, competition is higher. If abundant, lower.
    if current_supply < WATER_REQ * 1.1: # Very tight supply (e.g., supply < 14.3)
        if my_hp <= 7: # If HP is not great, be more aggressive
            bid_amount = max(bid_amount, DAILY_SALARY * 0.9) # 135
        else: # If HP is good, still need to be somewhat aggressive
            bid_amount = max(bid_amount, DAILY_SALARY * 0.7) # 105
    elif current_supply >= 25: # Abundant supply (MAX_SUPPLY is 25)
        if my_hp > 5: # If HP is good, try to save money
            bid_amount = min(bid_amount, DAILY_SALARY * 0.6) # 90
        # If HP is low, still prioritize winning despite abundant supply

    # Ensure bid doesn't exceed budget
    final_bid = min(my_status['budget'], bid_amount)

    # Ensure bid is at least 1 to participate
    return max(1.0, final_bid)
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

    # Calculate number of available water slots. Will almost always be 1.
    num_available_slots = int(current_supply / WATER_REQ)
    if num_available_slots == 0:
        num_available_slots = 1 # Assume at least one slot if supply > 0

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid minimum to win
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from active opponents, filtering for potentially strong ones
    yesterday_bids = []
    strong_opponents_yesterday_bids = []

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            # Heuristic for strong opponent: bid > 30% of my salary (45)
            if prev['bid'] > DAILY_SALARY * 0.3:
                strong_opponents_yesterday_bids.append(prev['bid'])

    # Determine a base bid
    base_bid = DAILY_SALARY * 0.55 # Default moderate bid (82.5)

    # Adjust base bid based on yesterday's competition
    if strong_opponents_yesterday_bids:
        highest_prev_strong_bid = max(strong_opponents_yesterday_bids)
        
        # If competition was very high yesterday
        if highest_prev_strong_bid >= DAILY_SALARY * 0.8: # 120
            if my_status['hp'] > 2: # If I have some buffer, try to conserve a bit
                base_bid = DAILY_SALARY * 0.6 
            else: # Must win, bid aggressively
                base_bid = DAILY_SALARY * 0.95 # 142.5
        
        # If competition was moderate to high
        elif highest_prev_strong_bid >= DAILY_SALARY * 0.4: # 60
            base_bid = max(base_bid, highest_prev_strong_bid + 2.0) # Bid slightly above
            base_bid = min(base_bid, DAILY_SALARY * 0.85) # Cap bid to prevent runaway (127.5)
        
        # If competition was low (but there were strong bids)
        else:
            base_bid = DAILY_SALARY * 0.4 # 60, try to save money
    else:
        # If no strong opponents or it's day 1, use a default competitive bid
        base_bid = DAILY_SALARY * 0.6 # 90

    # Adjust bid based on my HP
    if my_status['hp'] <= 1: # Critical HP, must win
        base_bid = DAILY_SALARY * 0.99 # Almost max bid (148.5)
    elif my_status['hp'] <= 2: # Low HP
        base_bid = max(base_bid, DAILY_SALARY * 0.9) # 135
    elif my_status['no_water_days'] > 0: # Missed water yesterday, need to win today
        base_bid = max(base_bid, DAILY_SALARY * 0.8) # 120

    # Adjust bid based on remaining days and budget
    remaining_days = EPISODE_DAYS - current_day + 1
    if remaining_days <= 2 and my_status['budget'] >= base_bid + DAILY_SALARY * 0.5: # Last 2 days, if budget allows to win comfortably
        base_bid = max(base_bid, DAILY_SALARY * 0.9) # Bid high to secure win

    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], base_bid)
    
    # Ensure bid is not negative or zero if budget is positive
    if final_bid <= 0 and my_status['budget'] > 0:
        return 1.0 # Minimum bid to stay in game if budget is low but positive
    elif final_bid <= 0 and my_status['budget'] <= 0:
        return 0.0 # No budget, can't bid

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

    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid low to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Determine highest previous bid from active opponents
    highest_prev_bid = 0.0
    prev_bids_count = 0
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev_trace['bid'])
            prev_bids_count += 1

    # Base bid strategy
    base_bid = DAILY_SALARY * 0.75 # A solid baseline

    # Adjust bid based on my HP and no_water_days
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        # Critical state: Bid very aggressively
        bid = DAILY_SALARY * 0.95
        if highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid + 5) # Try to outbid the highest opponent
    else:
        # Not critical, but still need water
        bid = base_bid

        # Adjust based on supply: higher competition for lower supply
        # Supply factor: 1 for min supply (15), 0 for max supply (25)
        supply_factor = 1.0
        if MAX_SUPPLY > MIN_SUPPLY:
            supply_factor = (MAX_SUPPLY - current_supply) / (MAX_SUPPLY - MIN_SUPPLY)
        
        # Increase bid when supply is low
        bid += (DAILY_SALARY * 0.2 * supply_factor) # Add up to 20% of salary based on supply scarcity

        # Adjust based on opponent's highest previous bid
        if highest_prev_bid > 0:
            # If highest previous bid is significant, try to beat it slightly
            if highest_prev_bid > DAILY_SALARY * 0.6: # If opponents are bidding high
                bid = max(bid, highest_prev_bid + 2)
            else: # If opponents are bidding low, don't overspend too much
                bid = max(bid, highest_prev_bid + 1)
        
        # If no previous bids from opponents, or they were very low, ensure a reasonable bid
        if highest_prev_bid == 0 and prev_bids_count > 0: # Opponents were alive but bid 0
            bid = max(bid, DAILY_SALARY * 0.5) # Assume they might start bidding
        elif prev_bids_count == 0 and num_alive_opponents > 0: # No trace, new opponents or first day
            bid = max(bid, DAILY_SALARY * 0.7) # Default aggressive bid

    # Final adjustments
    # Ensure bid does not exceed budget
    bid = min(bid, my_status['budget'])

    # Ensure bid is at least a minimal amount if I need water
    if bid < DAILY_SALARY * 0.1 and my_status['hp'] < 5:
         bid = min(my_status['budget'], DAILY_SALARY * 0.3)

    # Cap the bid to prevent overspending relative to salary, unless critical
    if my_status['hp'] > 2:
        bid = min(bid, DAILY_SALARY * 0.9)
    else: # If critical, can go higher
        bid = min(bid, DAILY_SALARY * 0.99)

    # Prevent bidding 0 if I need water and have budget
    if bid <= 0.01 and my_status['hp'] > 0 and my_status['budget'] > 0:
         bid = min(my_status['budget'], DAILY_SALARY * 0.1) # Bid a small amount if budget allows

    return round(bid, 2)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    current_supply = day_context['supply']
    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid - a safe amount to try and secure water
    bid_amount = DAILY_SALARY * 0.6

    # 1. No opponents alive: Bid low to save budget.
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.3)

    # Calculate total water needed by all alive agents (including myself)
    total_water_req_alive = WATER_REQ
    for opp in alive_opponents:
        total_water_req_alive += opp['water_requirement']

    # Get yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # 2. React to opponent's previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were aggressive, be more aggressive
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            bid_amount = max(bid_amount, highest_prev_bid * 1.05) # Try to slightly outbid
        else:
            # If bids were moderate, try to win by a small margin
            bid_amount = max(bid_amount, highest_prev_bid + 2.0) # Bid slightly above

    # 3. Adjust based on my HP (survival priority)
    if my_hp <= 2: # Critical HP, bid very aggressively
        bid_amount = max(bid_amount, DAILY_SALARY * 0.95)
    elif my_hp <= 5: # Low HP, bid aggressively
        bid_amount = max(bid_amount, DAILY_SALARY * 0.85)

    # 4. Adjust based on supply scarcity
    if current_supply < total_water_req_alive:
        # Supply is scarce, increase bid significantly
        bid_amount = max(bid_amount, DAILY_SALARY * 0.9)
        if yesterday_bids:
            bid_amount = max(bid_amount, max(yesterday_bids) * 1.1) # Even higher if yesterday was competitive
    else:
        # Supply is abundant, can be more conservative if not in critical HP
        if my_hp > 5: # If HP is good and supply is not scarce, we can try to save
            bid_amount = min(bid_amount, DAILY_SALARY * 0.7) # Reduce bid if safe

    # 5. Final check: Ensure bid doesn't exceed budget and is not negative
    final_bid = min(my_budget, bid_amount)
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
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid low to conserve budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Base bid: a percentage of daily salary
    base_bid = DAILY_SALARY * 0.5 # Moderate starting point

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] <= 6: # Medium HP
        base_bid = DAILY_SALARY * 0.65
    # If HP is high (above 6), keep base_bid as 0.5 * DAILY_SALARY

    # Adjust bid based on opponents' previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents were aggressive yesterday or I need water, bid higher
        if my_status['hp'] <= 4 or max_prev_bid > DAILY_SALARY * 0.7:
            base_bid = max(base_bid, max_prev_bid * 1.05) # Try to outbid the highest previous bid
        elif max_prev_bid > DAILY_SALARY * 0.4:
            base_bid = max(base_bid, avg_prev_bid * 1.01 + 5) # Slightly above average to compete
        else: # Opponents bid low, try to save money but still win
            base_bid = min(base_bid, avg_prev_bid * 1.1 + 1) # Bid slightly above average, but don't exceed my current base_bid if it's already higher

    # Adjust bid based on supply scarcity
    # How many full water_requirements can the supply satisfy?
    # CRITICAL INDEX RULE: supply is float, so int() for division
    potential_full_req_winners = int(day_context['supply'] // WATER_REQ)

    # If supply is tight (fewer slots than competitors + me)
    if potential_full_req_winners <= num_alive_opponents: # If supply can't satisfy everyone's full need
        if my_status['hp'] <= 4:
            base_bid = max(base_bid, DAILY_SALARY * 1.0) # Be very aggressive
        elif my_status['hp'] <= 6:
            base_bid = max(base_bid, DAILY_SALARY * 0.85)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.7)

    # End-game aggression
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] < 10: # Last 2 days and not perfectly healthy
        base_bid = max(base_bid, DAILY_SALARY * 1.0) # Bid high to secure survival

    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure bid is at least 1 if budget allows and not 0, unless budget is 0
    if final_bid < 1 and my_status['budget'] > 0:
        final_bid = 1.0
    elif my_status['budget'] == 0:
        final_bid = 0.0

    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150 # Cindy's daily salary

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid minimal to save budget
    if not alive_opponents:
        return min(my_status['budget'], 1.0) # Bid 1.0 to ensure I get water if there's any.

    # Collect yesterday's bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Critical HP or missed water days - bid very aggressively
    # This takes precedence over yesterday's bids if I'm desperate
    if my_status['no_water_days'] > 0 or my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95) # Bid 142.5

    # If there are yesterday's bids, react to them
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents bid very high (e.g., >= 127.5)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If my HP is good (> 3), try to save and let opponents overbid each other
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.3) # Bid 45
            # If my HP is not good (<= 3), I need to be aggressive
            return min(my_status['budget'], DAILY_SALARY * 0.9) # Bid 135 (high but slightly less than critical bid)
        
        # If opponents bid moderately or low (< 127.5)
        # Bid slightly above the highest previous bid, but at least DAILY_SALARY * 0.5 (75)
        # Using a buffer of 5.0 to ensure winning against slightly lower bids.
        return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 5.0))

    # If no yesterday's bids (e.g., first day of meta-round or no opponents bid)
    # Default bid based on my HP
    if my_status['hp'] <= 4: # Low HP, be moderately aggressive
        return min(my_status['budget'], DAILY_SALARY * 0.75) # Bid 112.5
    
    # Otherwise, bid moderately
    return min(my_status['budget'], DAILY_SALARY * 0.55) # Bid 82.5
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimally to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Given my WATER_REQ = 13 and supply_range = [15, 25],
    # only one agent can get their full 13 units of water.
    # This makes it a winner-take-all scenario for the most part.

    # Collect yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

    # Base bid: a moderate percentage of daily salary
    base_bid = DAILY_SALARY * 0.5

    # If there were previous bids, aim to outbid the highest one
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Bid slightly above the highest previous bid, or ensure it's at least a reasonable amount
        base_bid = max(base_bid, highest_prev_bid + 2.0) # Add a small buffer

    # Adjust bid based on my current HP
    # The lower my HP, the more aggressively I should bid
    if my_status['hp'] <= 2: # Critical HP: must win
        bid = min(my_status['budget'], DAILY_SALARY * 0.98, base_bid * 1.3) # Very aggressive
    elif my_status['hp'] <= 5: # Low HP: need to win
        bid = min(my_status['budget'], DAILY_SALARY * 0.85, base_bid * 1.15) # Aggressive
    else: # Healthy HP: try to conserve budget but still win
        bid = min(my_status['budget'], DAILY_SALARY * 0.7, base_bid * 1.05) # Moderately aggressive

    # Adjust bid based on day progression (pressure increases later in the game)
    current_day = day_context['day']
    if current_day >= EPISODE_DAYS - 2: # Last 2 days, bid very high to survive
        bid = min(my_status['budget'], bid * 1.2)
    elif current_day >= EPISODE_DAYS / 2: # Second half of the game
        bid = min(my_status['budget'], bid * 1.1)

    # Ensure bid is at least a minimal amount to be competitive, but not too low if only one slot is available
    min_competitive_bid = DAILY_SALARY * 0.3
    if len(alive_opponents) > 0:
        bid = max(bid, min_competitive_bid)

    # Final check: Bid must not exceed current budget
    return min(my_status['budget'], bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid strategy
    # Default to a competitive but not overly aggressive bid
    bid_amount = DAILY_SALARY * 0.6

    # Critical HP or missed water day: Bid aggressively
    if my_hp <= 2 or my_no_water_days >= 1:
        bid_amount = DAILY_SALARY * 0.95
    elif my_hp <= 4:
        bid_amount = DAILY_SALARY * 0.8

    # Adjust based on opponents' previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If highest previous bid was very high, react accordingly
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            # If I'm in a critical state, I must try to win
            if my_hp <= 2 or my_no_water_days >= 1:
                bid_amount = max(bid_amount, highest_prev_bid + 5)
            # Otherwise, be competitive but don't necessarily overbid if not critical
            else:
                bid_amount = max(bid_amount, highest_prev_bid * 0.9) # Try to win, but conserve if possible
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderate bids
            bid_amount = max(bid_amount, highest_prev_bid + 2)
        else: # Low bids
            bid_amount = max(bid_amount, highest_prev_bid + 1) # Just slightly above to win cheaply

    # Late game pressure: Increase bid to ensure survival
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 3:
        if my_hp < 5: # Low health in late game
            bid_amount = max(bid_amount, DAILY_SALARY * 0.9)
        elif my_hp >= 5 and my_budget > DAILY_SALARY * 2: # Healthy but want to secure water
            bid_amount = max(bid_amount, DAILY_SALARY * 0.75)
    elif remaining_days == 0: # Last day
        bid_amount = max(bid_amount, DAILY_SALARY * 0.99) # Bid almost all salary to survive

    # If no opponents, bid minimally to get water
    if not alive_opponents:
        bid_amount = DAILY_SALARY * 0.3

    # Ensure bid does not exceed current budget
    final_bid = min(my_budget, bid_amount)

    # Ensure a minimum bid to participate
    final_bid = max(final_bid, 1.0)

    return final_bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents are alive, bid minimally to save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], 5.0)

    # Calculate a baseline bid (fraction of daily salary)
    base_bid = DAILY_SALARY * 0.5

    # Adjust bid based on my HP
    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.75

    # Calculate total water requirement for all alive agents
    total_water_needed = WATER_REQ
    for opp in alive_opponents:
        total_water_needed += opp['water_requirement']

    # Adjust bid based on supply relative to total need
    if day_context['supply'] < total_water_needed: # Supply is less than total needed, high competition
        base_bid += DAILY_SALARY * 0.2
    elif day_context['supply'] < total_water_needed * 1.2: # Supply is somewhat tight
        base_bid += DAILY_SALARY * 0.1

    # Analyze opponent's previous bids from yesterday in the current episode
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    final_bid = base_bid # Default to base_bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # Opponents often exhaust budget quickly, so react to their aggression
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Very aggressive bidding detected
            if my_status['hp'] <= 3: # If my HP is low, I must compete strongly
                final_bid = max(base_bid, highest_prev_bid + 1.0)
            else: # If my HP is good, try to slightly underbid to save budget, but stay competitive
                final_bid = max(base_bid, highest_prev_bid * 0.95)
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderately aggressive
            final_bid = max(base_bid, average_prev_bid + 2.0)
        else: # Lower bids previously, maybe they are saving or supply was high
            final_bid = max(base_bid, average_prev_bid * 1.1)
    else: # No previous bids available (e.g., Day 1 of the episode)
        # On Day 1, use a default strategy based on observed meta-round behavior (aggressive early)
        if day_context['day'] == 1:
            final_bid = DAILY_SALARY * 0.65
        else:
            final_bid = base_bid # Fallback for other days without trace

    # Ensure bid does not exceed available budget and is at least 1.0
    return max(1.0, min(my_status['budget'], final_bid))
"""
