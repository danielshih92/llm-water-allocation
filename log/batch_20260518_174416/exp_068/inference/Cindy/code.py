# ============================================================
# Experiment: exp_068
# Agent: Cindy
# Source: exp_068
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQUIREMENT = 13
    MY_DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally
    if num_alive_opponents == 0:
        return min(my_status['budget'], 1)

    # Collect yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    else:
        # If no previous bids, assume a baseline for competition
        highest_prev_bid = MY_DAILY_SALARY * 0.4

    # Calculate demand vs supply pressure
    total_water_needed = MY_WATER_REQUIREMENT * (num_alive_opponents + 1)
    supply_pressure_multiplier = 1.0
    if day_context['supply'] < total_water_needed:
        # How much more water is needed than available, per player?
        shortage_ratio = total_water_needed / day_context['supply']
        supply_pressure_multiplier = min(shortage_ratio, 1.5) # Cap multiplier to avoid insane bids

    # My HP is critical (2 or less remaining)
    if my_status['hp'] <= 2:
        # Bid very aggressively to survive
        bid_amount = MY_DAILY_SALARY * 0.95 * supply_pressure_multiplier
        return min(my_status['budget'], max(1, bid_amount))

    # Check if any opponent is very low on HP (and I am not critical)
    any_opp_critical_hp = False
    for opp in alive_opponents:
        if opp['hp'] <= 2:
            any_opp_critical_hp = True
            break

    if any_opp_critical_hp and my_status['hp'] > 3:
        # If I'm relatively healthy and an opponent is desperate, I can try to outbid them
        base_bid = MY_DAILY_SALARY * 0.7 * supply_pressure_multiplier
        bid = max(base_bid, highest_prev_bid + 2)
        return min(my_status['budget'], bid)

    # General strategy based on yesterday's bids and supply pressure
    if highest_prev_bid >= MY_DAILY_SALARY * 0.8: # High competition yesterday
        if my_status['hp'] > 3: # Not critical, can afford to be slightly less aggressive
            base_bid = MY_DAILY_SALARY * 0.6
        else: # HP is getting low (3 or 4), need water
            base_bid = MY_DAILY_SALARY * 0.85
        bid_amount = max(base_bid, highest_prev_bid + 2) * supply_pressure_multiplier
    else: # Moderate to low competition yesterday
        base_bid = MY_DAILY_SALARY * 0.5
        bid_amount = max(base_bid, highest_prev_bid + 1) * supply_pressure_multiplier

    # Ensure bid is at least 1 and within budget
    return min(my_status['budget'], max(1, bid_amount))
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
    num_alive_competitors = len(alive_opponents) + 1 # Including myself

    # Base bid, adjusted by HP
    base_bid = DAILY_SALARY * 0.5 # Default moderate bid
    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.98 # Very aggressive
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.85 # Aggressive
    elif my_status['hp'] <= 6:
        base_bid = DAILY_SALARY * 0.7 # Moderately aggressive

    # Adjust for supply scarcity
    num_water_units_available = int(day_context['supply'] // WATER_REQ)
    if num_water_units_available < num_alive_competitors:
        # High competition: increase bid, especially if HP is not full
        if my_status['hp'] <= 8: # If not near full HP, be more aggressive
            base_bid = max(base_bid, DAILY_SALARY * 0.75)
        else: # If HP is good, but competition is high, still bid reasonably
            base_bid = max(base_bid, DAILY_SALARY * 0.6)
    elif num_water_units_available >= num_alive_competitors:
        # Low competition: can be more conservative if HP is good
        if my_status['hp'] > 8:
            base_bid = min(base_bid, DAILY_SALARY * 0.4) # Save budget
        elif my_status['hp'] > 6:
            base_bid = min(base_bid, DAILY_SALARY * 0.5) # Save a bit

    # React to opponents' previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If previous bids were high, we need to bid higher to win.
        # The margin depends on our HP.
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents were very aggressive
            if my_status['hp'] <= 4:
                base_bid = max(base_bid, highest_prev_bid + 7) # Need to win desperately
            else:
                base_bid = max(base_bid, highest_prev_bid + 2) # Slightly outbid
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderately aggressive
            base_bid = max(base_bid, highest_prev_bid * 1.05 + 1) # Outbid slightly
        else: # Conservative bids from opponents
            # We can afford to be slightly more conservative, but still aim to win
            base_bid = max(base_bid, highest_prev_bid * 1.1) # Still bid above to ensure win

    # Final bid ensures it doesn't exceed budget and is at least minimal
    final_bid = min(my_status['budget'], base_bid)

    # Ensure a minimum bid to participate, especially if HP is low
    if final_bid < 1.0 and my_status['hp'] < 10:
        final_bid = my_status['budget'] # Bid all if desperate
    elif final_bid < 0.1: # Minimum bid to participate if budget allows
        final_bid = 0.1

    # If no opponents, bid very low to save budget unless HP is critical
    if not alive_opponents:
        if my_status['hp'] < 10: # If not full HP
            final_bid = min(my_status['budget'], DAILY_SALARY * 0.2) # Bid a bit more to heal
        else:
            final_bid = min(my_status['budget'], DAILY_SALARY * 0.05) # Minimal bid to save budget
        final_bid = max(0.1, final_bid) # Ensure minimum bid

    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state, assuming constant for the round

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid strategy based on my HP
    # If HP is low, bid aggressively. If high, bid conservatively.
    bid_ratio = 0.5 # Default
    if my_status['hp'] <= 2:
        bid_ratio = 0.95 # Critical HP
    elif my_status['hp'] <= 5:
        bid_ratio = 0.75 # Low HP
    elif my_status['hp'] >= 8:
        bid_ratio = 0.35 # High HP, can save

    base_bid = DAILY_SALARY * bid_ratio

    # Adjust based on yesterday's highest bid from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest previous bid is significantly higher than my base, react
        if highest_prev_bid > base_bid * 1.2:
            base_bid = max(base_bid, highest_prev_bid + 1.0) # Try to outbid
        # If highest previous bid is significantly lower, I can be more conservative, but not too low
        elif highest_prev_bid < base_bid * 0.8:
            base_bid = min(base_bid, max(DAILY_SALARY * 0.1, highest_prev_bid - 1.0))

    # Adjust based on supply scarcity and number of competitors
    # Check if supply is sufficient for everyone to get their water_requirement
    required_for_all = (num_alive_opponents + 1) * WATER_REQ
    
    if day_context['supply'] < required_for_all:
        # Supply is scarce, competition will be high
        if my_status['hp'] <= 5: # If I'm in a bad state, bid very aggressively
            base_bid = max(base_bid, DAILY_SALARY * 0.9)
        else: # Otherwise, still bid higher than usual
            base_bid = max(base_bid, DAILY_SALARY * 0.6)
    else:
        # Supply is abundant, can potentially lower bid if HP is good
        if my_status['hp'] > 5 and num_alive_opponents > 0: # If doing well and there are opponents
            base_bid = min(base_bid, DAILY_SALARY * 0.4)
        elif num_alive_opponents == 0: # No opponents, bid minimum to survive
            base_bid = DAILY_SALARY / EPISODE_DAYS # Smallest sustainable bid

    # Ensure bid is within budget and non-negative
    final_bid = max(0.0, min(my_status['budget'], base_bid))

    # If I need water (not full HP), ensure bid is at least a minimal amount to participate
    if my_status['hp'] < EPISODE_DAYS:
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
    
    # Determine a base bid based on general conditions (supply and my HP)
    base_bid = DAILY_SALARY * 0.5 # Default moderate bid
    
    # Adjust base bid based on supply scarcity
    if day_context['supply'] <= WATER_REQ: # Very scarce, must be aggressive
        base_bid = DAILY_SALARY * 0.95
    elif day_context['supply'] < WATER_REQ * 2: # Tight supply
        base_bid = DAILY_SALARY * 0.75
    
    # Adjust base bid based on my HP, potentially overriding or boosting supply-based adjustment
    if my_status['hp'] <= 2: # Critical HP, must get water
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP, need to be strong
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no alive opponents, bid low to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were bidding very high yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.85: # Over 127.5
            if my_status['hp'] > 3: # Not critical, try to save while remaining competitive
                # Bid competitively, but try to get it cheaper than their max
                return min(my_status['budget'], max(base_bid, highest_prev_bid * 0.9))
            else: # Critical HP, must get water at almost any cost
                return min(my_status['budget'], DAILY_SALARY * 0.99) # Bid very high
        # If opponents were bidding moderately or low
        else:
            # Try to outbid them slightly, ensuring we meet our base needs
            return min(my_status['budget'], max(base_bid, highest_prev_bid + 5))
    
    # If no yesterday bids (e.g., Day 1, or opponents died/didn't bid)
    # Use the calculated base_bid as the primary bid
    return min(my_status['budget'], base_bid)
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
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], WATER_REQ * 1.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid_urgency_factor = 0.55
    if my_status['no_water_days'] >= 1:
        bid_urgency_factor = 0.95
    elif my_status['hp'] <= 2:
        bid_urgency_factor = 0.9
    elif my_status['hp'] <= 5:
        bid_urgency_factor = 0.8
    elif current_day >= EPISODE_DAYS - 2:
        bid_urgency_factor = 0.95

    base_bid = DAILY_SALARY * bid_urgency_factor

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.8 and bid_urgency_factor < 0.9:
            base_bid = max(base_bid, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.6 and bid_urgency_factor < 0.8:
            base_bid = max(base_bid, highest_prev_bid + 2)
        else:
            base_bid = max(base_bid, highest_prev_bid + 1)

    if current_supply < 2 * WATER_REQ:
        if bid_urgency_factor < 0.8:
            base_bid = max(base_bid, DAILY_SALARY * 0.7)

    final_bid = max(base_bid, WATER_REQ * 1.0)
    final_bid = min(final_bid, my_status['budget'])
    final_bid = max(final_bid, 0.0)

    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta_round_state
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    day = day_context['day']
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to get water
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # --- Calculate initial bid based on my status and day --- 
    current_bid = DAILY_SALARY * 0.4 # Base bid

    # Adjust bid based on my HP
    if my_hp <= 2: # Critical HP, bid very aggressively
        current_bid = DAILY_SALARY * 0.95
    elif my_hp == 3: # Low HP, bid strongly
        current_bid = DAILY_SALARY * 0.75
    elif my_no_water_days > 0: # If I missed water yesterday, increase bid slightly
        current_bid *= 1.1

    # Adjust bid based on remaining days (late game pressure)
    if day >= EPISODE_DAYS - 2: # Last few days, bid more aggressively
        current_bid *= 1.2
    elif day >= EPISODE_DAYS * 0.6: # Mid-to-late game
        current_bid *= 1.1

    # Adjust bid based on supply scarcity
    # If supply is very low, competition will be fierce
    if supply <= MIN_SUPPLY + 2: # e.g., 15-17
        current_bid *= 1.3
    elif supply <= MIN_SUPPLY + 5: # e.g., 18-20
        current_bid *= 1.1

    # Ensure a minimum bid even if my calculated bid is very low
    current_bid = max(current_bid, DAILY_SALARY * 0.1)

    # --- Incorporate opponent's previous behavior --- 
    highest_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])

    # If highest_prev_bid is significant and I need water, try to outbid it.
    # "Need water" criteria: low HP, missed water, or very scarce supply.
    needs_water_urgently = (my_hp <= 3 or my_no_water_days > 0 or supply <= MIN_SUPPLY + 5)

    if highest_prev_bid > 0 and needs_water_urgently:
        # If I need water urgently, ensure my bid is at least slightly above the highest previous bid.
        current_bid = max(current_bid, highest_prev_bid + 5)
    # If I don't urgently need water, my bid will reflect my lower urgency,
    # and I won't try to outbid the opponents' previous high bids.

    # Final adjustments and budget constraint
    final_bid = min(current_bid, my_budget)

    # If my budget is 0, I can't bid
    if my_budget <= 0:
        return 0.0

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
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], 1.0)

    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    competitive_floor_bid = 70.0 # Based on Eric's observed consistent bid

    # Use Eric's consistent bid as a baseline if no higher bid was observed yesterday
    effective_highest_prev_bid = max(highest_prev_bid, competitive_floor_bid)

    bid = 0.0
    remaining_days = EPISODE_DAYS - day_context['day']

    if my_status['hp'] <= 2: # Critically low health, bid aggressively
        bid = effective_highest_prev_bid + (DAILY_SALARY * 0.2)
        bid = max(bid, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4: # Low health, bid high
        bid = effective_highest_prev_bid + (DAILY_SALARY * 0.1)
        bid = max(bid, DAILY_SALARY * 0.75)
    else: # Healthy, more strategic bidding
        if remaining_days <= 3 and my_status['hp'] <= remaining_days + 1: # Late game, need to secure water
            bid = effective_highest_prev_bid + (DAILY_SALARY * 0.15)
            bid = max(bid, DAILY_SALARY * 0.85)
        elif my_status['hp'] > num_alive_opponents + 2: # Very healthy, can risk losing a day to save budget
            bid = effective_highest_prev_bid + 1.0
            bid = max(bid, DAILY_SALARY * 0.5)
        else: # Normal health, balanced approach
            bid = effective_highest_prev_bid + 2.0
            bid = max(bid, DAILY_SALARY * 0.6)

    bid = max(bid, 1.0)
    bid = min(bid, my_status['budget'])

    return bid
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
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid low to save budget
    if not alive_opponents:
        return max(1.0, min(my_budget, DAILY_SALARY * 0.1))

    # Identify strong opponents based on meta-round context
    # Bob and Eric survived all days with high average bids, indicating aggressive play.
    strong_opponent_ids = ["Bob", "Eric"]
    
    strong_opp_yesterday_bids = []
    all_opp_yesterday_bids = []

    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev_trace = opp.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                all_opp_yesterday_bids.append(prev_trace['bid'])
                if opp_id in strong_opponent_ids:
                    strong_opp_yesterday_bids.append(prev_trace['bid'])

    # --- Bidding strategy ---
    
    # 1. Base bid based on my HP (desperation)
    if my_hp <= 2: # Critical HP, must win
        bid = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP, high priority
        bid = DAILY_SALARY * 0.85
    else: # Moderate to good HP
        bid = DAILY_SALARY * 0.6 # Moderate starting point

    # 2. React to strong opponents' previous bids
    if strong_opp_yesterday_bids:
        max_strong_opp_bid = max(strong_opp_yesterday_bids)
        # If strong opponents bid high, we need to be competitive.
        # Adjust bid to be slightly above their max, more aggressively if my HP is low.
        if my_hp > 4: # If not critical, try to outbid them efficiently
            bid = max(bid, max_strong_opp_bid * 1.03)
        else: # If low HP, be more aggressive to secure water
            bid = max(bid, max_strong_opp_bid * 1.07)
    elif all_opp_yesterday_bids: # If no strong opponents, react to general highest bid
        max_all_opp_bid = max(all_opp_yesterday_bids)
        if my_hp > 4:
            bid = max(bid, max_all_opp_bid * 1.02)
        else:
            bid = max(bid, max_all_opp_bid * 1.05)


    # 3. Adjust for supply abundance/scarcity
    num_water_slots = int(current_supply // WATER_REQ)
    # Ensure num_water_slots is at least 1 if supply meets requirement
    if num_water_slots == 0 and current_supply >= WATER_REQ:
        num_water_slots = 1
    
    num_active_players = len(alive_opponents) + 1

    if num_water_slots >= num_active_players: # Enough water for everyone
        # Can afford to be less aggressive if HP is good
        if my_hp > 6:
            # Try to bid just enough to win against weaker players or a low default
            weak_opp_bids_only = [b for opp_id, opp in opponents_status.items()
                                  if opp['alive'] and opp_id not in strong_opponent_ids
                                  and opp.get('previous_trace', {}).get('bid') is not None
                                  for b in [opp['previous_trace']['bid']]]
            if weak_opp_bids_only:
                bid = min(bid, max(weak_opp_bids_only) * 1.02)
            else:
                bid = min(bid, DAILY_SALARY * 0.3) # Low bid if no specific weak bids
        
    elif num_water_slots < num_active_players and num_water_slots > 0: # Scarcity, but some can get water
        # Competition is high. Ensure bid is competitive.
        if my_hp <= 4: # If low HP, be very aggressive in scarcity
            bid = max(bid, DAILY_SALARY * 0.9)
        elif bid < DAILY_SALARY * 0.7: # If current bid is not very aggressive yet
            bid = max(bid, DAILY_SALARY * 0.7)

    # 4. Final checks and budget constraint
    bid = max(1.0, bid) # Minimum bid is 1.0
    bid = min(bid, my_budget) # Cannot bid more than budget

    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state, assuming it's constant.

    # Identify competitive opponents and their yesterday's bids
    competitive_bids_yesterday = []
    for agent_id, opp in opponents_status.items():
        if opp['alive']:
            # Based on LATEST METAROUND CONTEXT, Alex and Eric are competitive.
            # David is a clear non-threat with 0 bid, so ignore his bids.
            if agent_id == 'David':
                continue 

            prev_trace = opp.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                competitive_bids_yesterday.append(prev_trace['bid'])

    # Determine the base bid
    # Given that only one player can get water, I must bid to win every day.
    # Default aggressive bid if no strong competition history or for the first day
    base_bid = DAILY_SALARY * 0.9

    if competitive_bids_yesterday:
        highest_prev_bid = max(competitive_bids_yesterday)
        # Bid slightly higher than the highest opponent bid from yesterday to win.
        base_bid = highest_prev_bid + 1.0
        
        # Ensure the bid doesn't drop too low even if opponents underbid.
        # This floor ensures I still value water highly, given the critical nature.
        # A floor of 70% of salary seems reasonable to deter low-balling and secure water.
        base_bid = max(base_bid, DAILY_SALARY * 0.7)
    
    # Adjust bid based on my current HP
    # If HP is critically low (1 or 2 HP remaining), I must secure water at almost any cost.
    if my_status['hp'] <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.95) # Bid very aggressively

    # Adjust bid for endgame if I have a significant budget advantage
    remaining_days = EPISODE_DAYS - day_context['day'] + 1
    # If it's the last few days and I have enough budget to potentially outspend others for the remainder
    if remaining_days <= 3 and my_status['budget'] >= DAILY_SALARY * remaining_days:
        # If I can afford to pay full salary for remaining days, bid very high to secure the win.
        base_bid = max(base_bid, DAILY_SALARY * 0.98)
    
    # Ensure the bid does not exceed my current budget
    final_bid = min(my_status['budget'], base_bid)
    
    # Ensure the bid is at least 1.0 to be a valid, active bid.
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10 

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    bid_amount = DAILY_SALARY * 0.75 

    if my_hp <= 2:
        bid_amount = DAILY_SALARY * 1.05 
    elif my_hp == 3:
        bid_amount = DAILY_SALARY * 0.9
    elif my_hp >= 7:
        bid_amount = DAILY_SALARY * 0.65

    if my_no_water_days > 0:
        bid_amount = max(bid_amount, DAILY_SALARY * 1.1) 
        if my_no_water_days > 1:
            bid_amount = max(bid_amount, DAILY_SALARY * 1.25) 

    if current_supply <= MIN_SUPPLY + 3:
        bid_amount *= 1.1
    elif current_supply >= MAX_SUPPLY - 3:
        bid_amount *= 0.9

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            bid_amount = max(bid_amount, highest_prev_bid + 7)
        elif highest_prev_bid >= DAILY_SALARY * 0.75:
            bid_amount = max(bid_amount, highest_prev_bid + 3)
        else:
            bid_amount = max(bid_amount, highest_prev_bid + 1)

    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_hp < 5:
        bid_amount = max(bid_amount, my_budget * 0.9)

    final_bid = min(my_budget, bid_amount)

    if final_bid < DAILY_SALARY * 0.1 and my_budget > 0 and remaining_days > 0:
        final_bid = min(my_budget, DAILY_SALARY * 0.1)

    return final_bid
"""
