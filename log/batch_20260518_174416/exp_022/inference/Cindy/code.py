# ============================================================
# Experiment: exp_022
# Agent: Cindy
# Source: exp_022
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)
    total_competitors = num_alive_opponents + 1 # Myself + opponents

    current_supply = day_context['supply']
    current_day = day_context['day']

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    
    # Calculate how many agents *could* theoretically get water
    max_recipients = int(current_supply // WATER_REQ)

    # --- Strategy based on current state (Day 1 or no useful trace) ---
    base_bid = DAILY_SALARY * 0.5 # Default moderate bid (75)

    # Aggressive bidding if HP is low
    if my_hp <= 2:
        base_bid = DAILY_SALARY * 0.95 # Very high bid (142.5)
    elif my_hp <= 3:
        base_bid = DAILY_SALARY * 0.8 # High bid (120)

    # Adjust bid based on supply scarcity and competition
    if max_recipients < total_competitors: # Supply is scarce relative to demand
        if my_hp > 3: # If not critical HP, increase bid to be more competitive
            base_bid = max(base_bid, DAILY_SALARY * 0.7) # (105)
        
        # If supply is very tight (e.g., only one person can get water)
        if max_recipients == 1 and total_competitors > 1:
            base_bid = max(base_bid, DAILY_SALARY * 0.85) # (127.5)
            
    elif max_recipients >= total_competitors: # Supply is abundant
        if my_hp > 3: # If not critical HP, we can afford to bid lower
            base_bid = min(base_bid, DAILY_SALARY * 0.4) # (60)
        elif my_hp > 2: # Slightly higher than very low
            base_bid = min(base_bid, DAILY_SALARY * 0.5) # (75)

    # --- Incorporate opponent previous trace if available (for subsequent days) ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents are bidding very high, we might need to match or slightly exceed
        # unless our HP is good and supply is abundant.
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents are bidding aggressively
            if my_hp <= 3: # My HP is low, I must compete
                base_bid = max(base_bid, highest_prev_bid + 5) # Try to outbid
            elif max_recipients < total_competitors: # Supply is scarce
                base_bid = max(base_bid, highest_prev_bid + 2)
            else: # Supply is abundant, maybe don't engage in bidding war
                base_bid = min(base_bid, DAILY_SALARY * 0.6) # Still competitive but not overpaying
        elif highest_prev_bid <= DAILY_SALARY * 0.3: # Opponents are bidding very low
            if max_recipients >= total_competitors: # Supply is abundant
                base_bid = min(base_bid, highest_prev_bid + 1) # Bid slightly above to secure
            else: # Supply is scarce, don't follow low bids if I need water
                base_bid = max(base_bid, DAILY_SALARY * 0.6) # Maintain a reasonable bid

    # Ensure bid does not exceed budget
    final_bid = min(my_budget, base_bid)

    # Ensure bid is non-negative
    final_bid = max(0.0, final_bid)

    return float(final_bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)
    total_players = num_alive_opponents + 1

    # Base bid calculation based on HP
    my_bid = DAILY_SALARY * 0.45 # Default bid if healthy

    if my_hp <= 2: # Critical HP, must get water
        my_bid = DAILY_SALARY * 0.95
    elif my_hp == 3: # Low HP
        my_bid = DAILY_SALARY * 0.8
    elif my_hp == 4: # Moderate HP
        my_bid = DAILY_SALARY * 0.65

    # Incorporate previous day's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Very high competition
            if my_hp <= 4: # Low to moderate HP, need to fight for water
                my_bid = max(my_bid, highest_prev_bid + (DAILY_SALARY * 0.05)) # Bid higher
            else: # Healthy, but still acknowledge high competition
                my_bid = max(my_bid, highest_prev_bid * 0.95) # Competitive, try to get slightly cheaper
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderate competition
            if my_hp <= 3:
                my_bid = max(my_bid, highest_prev_bid + (DAILY_SALARY * 0.03))
            else:
                my_bid = max(my_bid, highest_prev_bid * 0.9) # Try to undercut slightly
        else: # Low competition
            my_bid = max(my_bid, highest_prev_bid * 1.1) # Bid slightly above to secure

    # Adjust for supply scarcity
    estimated_total_water_needed = WATER_REQ * total_players
    if supply < estimated_total_water_needed * 0.75: # Supply is tight
        if my_hp <= 4:
            my_bid = max(my_bid, DAILY_SALARY * 0.7) # Increase bid to secure water
        else:
            my_bid = max(my_bid, DAILY_SALARY * 0.55) # Still increase, but less aggressively

    # Adjust for end of episode urgency
    days_left = EPISODE_DAYS - current_day
    if days_left <= 2: # Last two days, survival is key
        if my_hp > 1: 
            my_bid = max(my_bid, DAILY_SALARY * 0.9)
    elif days_left <= 4: # Approaching end
        if my_hp > 2:
            my_bid = max(my_bid, DAILY_SALARY * 0.75)

    # Ensure bid does not exceed budget
    my_bid = min(my_budget, my_bid)
    
    # Ensure a minimum bid if budget allows and I need water
    if my_budget > 0 and my_hp < 5: 
        my_bid = max(my_bid, DAILY_SALARY * 0.1)

    # Ensure bid is non-negative
    my_bid = max(0.0, my_bid)

    return float(my_bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10
    MAX_HP = 10 # Assuming starting HP

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid conservatively to secure water and save budget
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Collect yesterday's bids from active opponents in the current meta-round
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # 1. Determine base bid based on my health and need for water
    if my_hp <= 2: # Critical HP
        my_bid = DAILY_SALARY * 0.98 # Very aggressive
    elif my_no_water_days >= 1: # Missed water yesterday
        my_bid = DAILY_SALARY * 0.90 # Aggressive
    elif my_hp <= 4: # Low HP
        my_bid = DAILY_SALARY * 0.80
    else: # Healthy HP
        my_bid = DAILY_SALARY * 0.50 # Moderate base bid

    # 2. Adjust bid based on supply scarcity and opponent's highest previous bid
    num_my_water_units = int(current_supply // WATER_REQ)

    if num_my_water_units < 2: # Supply is scarce (high competition for 1 unit)
        # If desperate, outbid previous high aggressively
        if my_hp <= 4 or my_no_water_days >= 1:
            my_bid = max(my_bid, highest_prev_bid + 5)
        else:
            # Healthy but high competition, still bid robustly
            my_bid = max(my_bid, highest_prev_bid + 2, DAILY_SALARY * 0.65) # Ensure it's not too low
    else: # Supply is more abundant (enough for 2 or more units)
        # If desperate, slightly outbid previous high
        if my_hp <= 4 or my_no_water_days >= 1:
            my_bid = max(my_bid, highest_prev_bid + 1)
        else:
            # Healthy and abundant supply, try to save money.
            # Only outbid if opponent's bid is low, otherwise try to get it cheaper.
            if highest_prev_bid > DAILY_SALARY * 0.6: # Opponent is bidding high
                my_bid = min(my_bid, highest_prev_bid * 0.9) # Try to get it cheaper
            else: # Opponent is bidding low or moderately
                my_bid = min(my_bid, DAILY_SALARY * 0.35) # Conservative bid

    # 3. Apply budget constraints and minimum bid
    my_bid = max(1.0, my_bid) # Minimum bid to participate
    my_bid = min(my_budget, my_bid) # Cannot exceed budget

    # 4. Apply long-term budget management, but only if not critical HP
    if my_hp > 2: # Only if not critically low on HP
        remaining_days = EPISODE_DAYS - current_day + 1
        if remaining_days > 0:
            affordable_per_day = my_budget / remaining_days
            # If budget is tight for remaining days, scale back bid
            if affordable_per_day < DAILY_SALARY * 0.4:
                my_bid = min(my_bid, affordable_per_day * 0.8)
            elif affordable_per_day < DAILY_SALARY * 0.6:
                my_bid = min(my_bid, affordable_per_day * 0.9)
    
    # Ensure bid is not zero if I have budget and need water
    if my_bid == 0 and my_budget > 0 and my_hp < MAX_HP:
        my_bid = min(my_budget, DAILY_SALARY * 0.1)

    return float(my_bid)
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
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid - a safe starting point
    base_bid = DAILY_SALARY * 0.6

    # If no opponents, bid minimally to save budget
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    # --- Survival Priority --- 
    if my_hp <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.99 # Bid almost full salary to survive
    elif my_no_water_days >= 1: # Missed water yesterday, need it today
        base_bid = DAILY_SALARY * 0.90
    elif my_hp <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.75

    # --- Competition Analysis --- 
    num_water_slots = int(current_supply / WATER_REQ)

    if num_water_slots == 0: # No one can get full water, save budget if possible
        if my_hp <= 1: # Desperate for any water, even partial
            base_bid = DAILY_SALARY * 0.95
        else:
            # If not critical, bid low to save budget, but ensure we participate if budget allows
            return min(my_budget, DAILY_SALARY * 0.1)

    if num_alive_opponents > 0:
        if num_water_slots <= num_alive_opponents: # High competition (fewer slots than players)
            base_bid *= 1.15 # Increase bid significantly
        elif num_water_slots > num_alive_opponents + 1: # Low competition (many slots)
            base_bid *= 0.85 # Decrease bid to save budget

    # --- React to Opponent's Previous Bids --- 
    yesterday_bids = []
    for opp_data in alive_opponents:
        prev_trace = opp_data.get('previous_trace')
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If highest bid yesterday was very high, it signals aggressive play
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_hp <= 3: # If critical, try to outbid
                base_bid = max(base_bid, highest_prev_bid + 10)
            else: # Otherwise, match or slightly below if not critical
                base_bid = max(base_bid, highest_prev_bid * 0.95)
        elif highest_prev_bid > base_bid * 0.8: # Moderate high bid
            base_bid = max(base_bid, highest_prev_bid + 2) # Slightly outbid

    # --- Late Game Strategy --- 
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last two days
        if my_hp <= 5: # Ensure survival
            base_bid = max(base_bid, DAILY_SALARY * 1.05) # Bid more than salary if needed
        elif my_budget > DAILY_SALARY * 2: # If budget is good, can afford to be more aggressive
            base_bid = max(base_bid, DAILY_SALARY * 0.8)

    # Final bid must be within budget and at least 1 (if budget allows)
    final_bid = min(my_budget, base_bid)
    final_bid = max(final_bid, 1.0) if my_budget >= 1.0 else my_budget # Ensure at least 1 if budget permits, else bid what's left

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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    strong_opponent_bids = []
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive'] and opp_id in ["Alex", "Eric"]:
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                strong_opponent_bids.append(prev['bid'])
        elif opp_data['alive']:
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None and prev['bid'] > DAILY_SALARY * 0.8:
                strong_opponent_bids.append(prev['bid'])

    target_bid = DAILY_SALARY * 0.9

    if strong_opponent_bids:
        highest_prev_strong_bid = max(strong_opponent_bids)
        target_bid = highest_prev_strong_bid + 2.5
        target_bid = max(target_bid, DAILY_SALARY * 0.85)
    else:
        if len(alive_opponents) > 0:
            target_bid = DAILY_SALARY * 0.9
        else:
            target_bid = DAILY_SALARY * 0.1

    if my_hp <= 2:
        final_bid = max(target_bid * 1.1, DAILY_SALARY * 1.15)
    elif my_hp <= 4:
        final_bid = max(target_bid * 1.05, DAILY_SALARY * 1.05)
    else:
        if current_day <= EPISODE_DAYS / 2:
            final_bid = target_bid
        else:
            if my_budget > DAILY_SALARY * 2:
                final_bid = target_bid
            else:
                final_bid = target_bid * 0.95

    if len(alive_opponents) > 0:
        final_bid = max(final_bid, DAILY_SALARY * 0.3)

    return max(0.0, min(my_budget, final_bid))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13
    EPISODE_DAYS = 10
    
    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Base bid
    bid = DAILY_SALARY * 0.6 # Default to 90
    
    # Adjust for desperation
    if my_no_water_days >= 1 or my_hp <= 3: # If I missed water yesterday or HP is low
        bid = DAILY_SALARY * 0.9 # Bid 135
    if my_hp <= 1: # Extreme desperation
        bid = DAILY_SALARY * 0.95 # Bid 142.5

    # Adjust based on opponent activity
    if not alive_opponents:
        bid = DAILY_SALARY * 0.3 # No competition, bid low (45)
    else:
        yesterday_bids = []
        strong_opponents_bids = []
        for opp_id, opp in opponents_status.items():
            if opp['alive']:
                prev = opp.get('previous_trace', {})
                if prev and prev.get('bid') is not None:
                    yesterday_bids.append(prev['bid'])
                    if opp_id in ["Alex", "David"]: # Focus on strong opponents identified from meta-round context
                        strong_opponents_bids.append(prev['bid'])
        
        if strong_opponents_bids:
            highest_strong_bid = max(strong_opponents_bids)
            # If strong opponents bid high, I need to counter
            if highest_strong_bid >= DAILY_SALARY * 0.8: # If they bid >= 120
                if my_hp > 3: # Not too desperate, but need to compete
                    bid = max(bid, highest_strong_bid + 5) # Bid slightly above them
                else: # Desperate, bid even higher
                    bid = max(bid, highest_strong_bid + 10) # Bid more aggressively
            elif highest_strong_bid >= DAILY_SALARY * 0.5: # If they bid between 75 and 120
                bid = max(bid, highest_strong_bid + 2) # Slightly above
        elif yesterday_bids: # If no strong opponents, but other opponents exist
            highest_other_bid = max(yesterday_bids)
            if highest_other_bid >= DAILY_SALARY * 0.4: # If other opponents bid >= 60
                bid = max(bid, highest_other_bid + 1) # Just a bit higher

    # Late game desperation
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        if my_hp > 1: # Still have some buffer, but need to survive
            bid = max(bid, DAILY_SALARY * 0.8) # Bid 120
        else: # Very desperate, must get water
            bid = max(bid, DAILY_SALARY * 0.95) # Bid 142.5

    # Ensure bid doesn't exceed budget
    final_bid = min(my_budget, bid)
    
    # Ensure bid is at least 0
    return max(0.0, final_bid)
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

    # Base bid - a moderate amount
    base_bid = DAILY_SALARY * 0.5

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical health
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low health
        base_bid = DAILY_SALARY * 0.75
    elif my_status['hp'] <= 6 and day_context['day'] > EPISODE_DAYS / 2: # Mid-game, slightly low HP
        base_bid = DAILY_SALARY * 0.65

    # Adjust bid based on supply: more competition if supply is low
    # Supply range is [15, 25]. My requirement is 13.
    if day_context['supply'] <= WATER_REQ + 5: # Supply is tight (e.g., 15-18)
        base_bid = max(base_bid, DAILY_SALARY * 0.6) # Increase base bid if supply is scarce
    elif day_context['supply'] >= 20: # Supply is relatively abundant (e.g., 20-25)
        # Only reduce base bid if not already desperate
        if my_status['hp'] > 4:
            base_bid = min(base_bid, DAILY_SALARY * 0.45) # Decrease base bid if supply is high

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    proposed_bid = base_bid

    # Adjust bid based on opponent's previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If my HP is low or I'm already aiming for an aggressive bid, try to win
        if my_status['hp'] <= 4 or proposed_bid >= DAILY_SALARY * 0.7:
            proposed_bid = max(proposed_bid, highest_prev_bid + 2.0) # Bid slightly above highest previous
        else:
            # If highest bid was very high, but I'm not desperate, maybe don't match it fully
            if highest_prev_bid > DAILY_SALARY * 0.8:
                proposed_bid = max(proposed_bid, DAILY_SALARY * 0.6) # Don't overbid if not critical
            else:
                proposed_bid = max(proposed_bid, highest_prev_bid + 1.0) # Bid slightly above

    # Final check: ensure bid doesn't exceed budget and is at least 0
    final_bid = min(my_status['budget'], proposed_bid)
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

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

    bid = 0.0

    if my_status['hp'] <= 3:
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 6:
        if highest_prev_bid > DAILY_SALARY * 0.6:
            bid = max(DAILY_SALARY * 0.75, highest_prev_bid + 2.0)
        else:
            bid = DAILY_SALARY * 0.7
    else:
        if highest_prev_bid > DAILY_SALARY * 0.5:
            bid = max(DAILY_SALARY * 0.6, highest_prev_bid + 1.5)
        else:
            bid = DAILY_SALARY * 0.55

    final_bid = min(my_status['budget'], bid)
    final_bid = max(0.0, final_bid)

    if final_bid < DAILY_SALARY * 0.3 and my_status['budget'] >= DAILY_SALARY * 0.3:
        final_bid = DAILY_SALARY * 0.3

    return float(final_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10

    # Base bid: a reasonable amount to secure water if no strong competition
    base_bid = DAILY_SALARY * 0.6

    # Identify active and historically aggressive opponents
    # Based on LATEST METAROUND CONTEXT, Eric is the primary threat. Alex is secondary.
    threat_opponents_ids = ["Eric", "Alex"]
    
    highest_prev_threat_bid = 0.0
    for opp_id in threat_opponents_ids:
        if opp_id in opponents_status and opponents_status[opp_id]['alive']:
            opp_data = opponents_status[opp_id]
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                highest_prev_threat_bid = max(highest_prev_threat_bid, prev_trace['bid'])

    current_bid = base_bid

    # 1. Desperation logic (my HP is low or I haven't gotten water for a day)
    if my_status['no_water_days'] >= 1 or my_status['hp'] <= 2:
        current_bid = DAILY_SALARY * 0.95 # Bid very high
    elif my_status['hp'] <= 4: # Getting low
        current_bid = DAILY_SALARY * 0.85 # Bid high

    # 2. React to opponent's previous high bid
    if highest_prev_threat_bid > 0:
        if highest_prev_threat_bid >= DAILY_SALARY * 0.8: # Opponent bid very high yesterday
            if my_status['hp'] > 4 and my_status['no_water_days'] == 0:
                # If I'm not desperate and opponent overbid, try to save money
                current_bid = min(current_bid, DAILY_SALARY * 0.5) # Try to get it cheaper
            else:
                # I need water, so I must outbid or match them
                current_bid = max(current_bid, highest_prev_threat_bid + 5.0)
        else: # Opponent's previous bid was moderate or low
            current_bid = max(current_bid, highest_prev_threat_bid + 1.5) # Try to outbid them slightly

    # 3. Adjust bid based on supply scarcity
    # If supply is just enough for one person (13-15), competition is fierce
    # If supply is enough for two persons (25), competition is still there but less direct
    if day_context['supply'] <= WATER_REQ + 2: # Supply is very tight (e.g., 15)
        if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1: # If desperate and supply is low
            current_bid = max(current_bid, DAILY_SALARY * 0.9) # Be very aggressive
        else: # Not desperate but supply is low
            current_bid = max(current_bid, DAILY_SALARY * 0.75) # Be aggressive

    # 4. End game strategy: if it's nearing the end, be more aggressive if needed
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: # Last few days
        if my_status['hp'] <= (remaining_days * 1.5): # Need to ensure survival
            current_bid = max(current_bid, DAILY_SALARY * 0.98) # Bid almost everything if needed

    # Ensure bid doesn't exceed budget and is at least a minimal amount
    current_bid = max(1.0, min(current_bid, my_status['budget']))

    # Round the bid to avoid tiny floats
    return float(round(current_bid, 2))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
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

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    strong_opponents_ids = {"Alex", "David"} 
    
    yesterday_strong_bids = []
    yesterday_all_bids = []

    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_all_bids.append(prev['bid'])
                if opp_id in strong_opponents_ids:
                    yesterday_strong_bids.append(prev['bid'])

    max_yesterday_strong_bid = 0
    if yesterday_strong_bids:
        max_yesterday_strong_bid = max(yesterday_strong_bids)

    max_yesterday_all_bid = 0
    if yesterday_all_bids:
        max_yesterday_all_bid = max(yesterday_all_bids)

    num_strong_opponents_alive = len([o for o_id, o in opponents_status.items() if o['alive'] and o_id in strong_opponents_ids])
    
    bid = DAILY_SALARY * 0.6 

    if my_hp <= 3 or my_no_water_days >= 1:
        bid = DAILY_SALARY * 1.05 
        if max_yesterday_strong_bid > 0:
            bid = max(bid, max_yesterday_strong_bid + 7) 
        elif max_yesterday_all_bid > 0:
            bid = max(bid, max_yesterday_all_bid + 5) 
        
        if my_hp <= 2:
            bid = max(bid, DAILY_SALARY * 1.15)
            if max_yesterday_strong_bid > 0:
                bid = max(bid, max_yesterday_strong_bid + 15) 
        
        return min(my_budget, bid)

    if num_strong_opponents_alive > 0:
        bid = DAILY_SALARY * 0.8 
        if max_yesterday_strong_bid > 0:
            bid = max(bid, max_yesterday_strong_bid + 3) 
        else:
            bid = max(bid, DAILY_SALARY * 0.75)
    else:
        bid = DAILY_SALARY * 0.5
        if max_yesterday_all_bid > 0:
            bid = max(bid, max_yesterday_all_bid + 1)
            if max_yesterday_all_bid > DAILY_SALARY * 0.7:
                bid = min(bid, DAILY_SALARY * 0.75) 
        else:
            bid = DAILY_SALARY * 0.3 

    remaining_days = EPISODE_DAYS - current_day + 1 
    if remaining_days > 0 and my_budget / remaining_days < DAILY_SALARY * 0.6:
        if my_hp > 5: 
            bid = min(bid, my_budget / remaining_days * 1.1)
            bid = max(bid, DAILY_SALARY * 0.3) 
        else: 
            bid = max(bid, DAILY_SALARY * 0.9) 

    bid = max(bid, DAILY_SALARY / WATER_REQ * 5) 

    bid = max(1.0, min(my_budget, bid))
    return bid
"""
