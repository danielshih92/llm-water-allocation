# ============================================================
# Experiment: exp_087
# Agent: Cindy
# Source: exp_087
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_supply = day_context['supply']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_competitors = len(alive_opponents)
    total_agents_in_game = num_competitors + 1 # Me + alive opponents

    # Calculate how many agents can theoretically get their full water requirement
    num_possible_winners = int(current_supply // WATER_REQ)

    # Base bid
    bid = DAILY_SALARY * 0.5 # Default to 50% of salary (75)

    # 1. Urgency based on my HP
    if my_hp <= 1: # Critical HP, bid very high
        bid = DAILY_SALARY * 0.95
    elif my_hp <= 3: # Moderate risk HP, bid high
        bid = DAILY_SALARY * 0.75

    # 2. Adjust bid based on supply and competition
    if num_possible_winners < total_agents_in_game:
        # Supply is tight, competition is high
        if my_hp > 3: # If healthy, still need to be competitive but not desperate
            bid = max(bid, DAILY_SALARY * 0.65) # Ensure a decent bid
        # If HP is already low, the above HP-based bid will be higher
    else:
        # Supply is ample, competition is lower
        if my_hp > 3: # If healthy, try to save money
            bid = min(bid, DAILY_SALARY * 0.4) # Try to get it cheaper
        # If HP is low, still prioritize getting water, so don't lower bid too much

    # 3. Adjust bid based on yesterday's opponent behavior
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If highest previous bid was very aggressive, and supply is tight, react
        if num_possible_winners < total_agents_in_game:
            if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents were aggressive
                if my_hp <= 3: # I need water
                    bid = max(bid, highest_prev_bid + 1) # Bid slightly above
                else: # Healthy, but need to stay in game
                    bid = max(bid, highest_prev_bid * 0.9) # Be competitive
            elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderately aggressive
                bid = max(bid, highest_prev_bid + 0.5)
        else:
            # Ample supply, try to win cheaply if opponents bid low
            if highest_prev_bid < DAILY_SALARY * 0.5:
                bid = max(bid, highest_prev_bid + 0.1) # Just barely win
            elif highest_prev_bid >= DAILY_SALARY * 0.7: # Opponents overbid for ample supply
                if my_hp > 3: # If healthy, don't overbid
                    bid = min(bid, DAILY_SALARY * 0.5) # Try to get it cheaper

    # Ensure bid does not exceed budget
    final_bid = min(my_budget, bid)

    # Ensure a minimum bid to stay relevant, but not too low to be ignored
    if final_bid <= 0 and my_budget > 0:
        final_bid = 1 # Always bid at least 1 if budget allows
    elif my_budget == 0:
        final_bid = 0

    return round(final_bid, 2)
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    supply = day_context['supply']

    # Base bid calculation
    # Start with a strong bid, as water is always scarce in this scenario
    bid = DAILY_SALARY * 0.75

    # Adjust bid based on my current health (lower HP -> more aggressive bid)
    if my_hp <= 2: # Critical health
        bid = DAILY_SALARY * 0.98 # Bid almost full salary to survive
    elif my_hp <= 4: # Low health
        bid = DAILY_SALARY * 0.90
    elif my_hp <= 6: # Medium health
        bid = DAILY_SALARY * 0.80
    else: # Healthy
        bid = DAILY_SALARY * 0.70

    # Adjust bid based on the day (increasing pressure towards the end of the meta-round)
    if current_day >= EPISODE_DAYS * 0.8: # Last 20% of days
        bid *= 1.1 # Increase bid by 10%
    elif current_day >= EPISODE_DAYS * 0.6: # Middle-late game
        bid *= 1.05 # Increase bid by 5%

    # Analyze opponents' previous bids and current status to gauge competition
    highest_potential_opponent_bid = 0.0
    num_alive_opponents = 0

    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            num_alive_opponents += 1
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                # Consider what the opponent *could* realistically bid today, capped by their current budget.
                # This handles cases like Alex who had a high max_bid yesterday but low current budget.
                opponent_realistic_bid_today = min(prev_trace['bid'], opp_data['budget'])
                highest_potential_opponent_bid = max(highest_potential_opponent_bid, opponent_realistic_bid_today)
            else:
                # If no previous bid, assume they might bid around half their salary if they have budget
                if opp_data['budget'] > DAILY_SALARY * 0.5:
                    highest_potential_opponent_bid = max(highest_potential_opponent_bid, DAILY_SALARY * 0.6)

    # If there's a strong opponent bid from yesterday (or estimated), react to it.
    if highest_potential_opponent_bid > 0:
        # Increase bid to beat the highest potential opponent bid, especially if my HP is low.
        if my_hp <= 4:
            bid = max(bid, highest_potential_opponent_bid * 1.02) # Bid 2% higher to secure water
        else:
            bid = max(bid, highest_potential_opponent_bid + 1.0) # Bid slightly higher to win

    # If competition is very low (only me, or me + one other), try to save money if not critical.
    if num_alive_opponents == 0: # Only me left
        bid = DAILY_SALARY * 0.1 # Minimal bid to save budget
    elif num_alive_opponents == 1: # Me + one other opponent
        if my_hp > 4: # If relatively healthy, try to save money
            bid = min(bid, DAILY_SALARY * 0.65) # Cap bid to prevent overspending against a single opponent

    # Adjust for supply scarcity: if water is very scarce compared to competitors, increase bid.
    # 'potential_winners' is the number of people who could get water if everyone needed full water_req.
    potential_winners = int(supply / WATER_REQ)
    # If not enough water for everyone competing (including myself)
    if potential_winners < num_alive_opponents + 1:
        # The more competitors than available water portions, the higher the pressure.
        # This factor pushes bids up, but is capped to prevent extreme bids.
        scarcity_multiplier = 1.0 + (num_alive_opponents + 1 - potential_winners) * 0.03
        bid *= scarcity_multiplier
        bid = min(bid, DAILY_SALARY * 0.99) # Cap the bid due to scarcity

    # Ensure the final bid does not exceed my current budget
    final_bid = min(my_budget, bid)

    # Ensure the bid is non-negative
    return max(0.0, final_bid)
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_budget, 1.0)

    remaining_days = EPISODE_DAYS - current_day + 1

    base_bid = DAILY_SALARY * 0.5 

    if my_hp <= 2:
        base_bid = DAILY_SALARY * 0.95
        if my_no_water_days > 0:
            base_bid = DAILY_SALARY * 1.0 
    elif my_hp <= 4:
        base_bid = DAILY_SALARY * 0.75
    elif my_no_water_days > 0:
        base_bid = DAILY_SALARY * 0.65

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_hp <= 3:
                base_bid = max(base_bid, highest_prev_bid + 5.0)
            else:
                base_bid = max(base_bid, highest_prev_bid + 2.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            base_bid = max(base_bid, highest_prev_bid + 1.0)

    if current_day < EPISODE_DAYS / 3:
        if my_hp > 5:
            base_bid = min(base_bid, DAILY_SALARY * 0.7)
    elif current_day > EPISODE_DAYS * 2 / 3:
        if my_hp <= 5:
            base_bid = max(base_bid, DAILY_SALARY * 0.85)

    final_bid = base_bid

    max_affordable_bid = my_budget - 0.01
    final_bid = min(final_bid, max_affordable_bid)

    if remaining_days > 0 and my_budget / remaining_days < DAILY_SALARY * 0.7 and my_hp > 3:
        if highest_prev_bid > DAILY_SALARY * 0.8:
            final_bid = min(final_bid, DAILY_SALARY * 0.4)
        else:
            final_bid = min(final_bid, DAILY_SALARY * 0.6)
    
    final_bid = max(0.01, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13
    EPISODE_DAYS = 10

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    days_remaining = EPISODE_DAYS - current_day

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid = DAILY_SALARY * 0.65 

    if not yesterday_bids:
        if my_hp <= 3:
            bid = DAILY_SALARY * 0.9
        elif my_hp <= 5:
            bid = DAILY_SALARY * 0.8
        else:
            bid = DAILY_SALARY * 0.7
    else:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_hp <= 3:
                bid = max(highest_prev_bid + 10, DAILY_SALARY * 0.98)
            elif my_hp <= 5:
                bid = max(highest_prev_bid + 5, DAILY_SALARY * 0.9)
            else:
                bid = max(highest_prev_bid * 0.95, DAILY_SALARY * 0.7)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            if my_hp <= 4:
                bid = max(highest_prev_bid + 3, DAILY_SALARY * 0.8)
            else:
                bid = max(highest_prev_bid + 1, DAILY_SALARY * 0.65)
        else:
            bid = max(highest_prev_bid + 1, DAILY_SALARY * 0.4)

    if my_hp <= 2:
        bid = max(bid, DAILY_SALARY * 1.0)
    elif my_hp <= 4:
        bid = max(bid, DAILY_SALARY * 0.9)

    if days_remaining <= 2:
        bid = max(bid, DAILY_SALARY * 0.95)
    elif days_remaining <= 4:
        bid = max(bid, DAILY_SALARY * 0.8)

    if current_supply <= 17:
        bid *= 1.1
    elif current_supply >= 23:
        if my_hp > 5 and days_remaining > 3:
            bid *= 0.9

    final_bid = min(my_budget, bid)
    
    return max(0.1, final_bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimal to secure water
    if not alive_opponents:
        return min(my_budget, 1.0)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # Base bid will be influenced by my HP and the need to survive
    bid_to_win = 0.0

    # If I'm in critical condition (HP <= 1) or missed water yesterday, bid very high
    if my_hp <= 1 or my_no_water_days > 0:
        bid_to_win = DAILY_SALARY * 0.95
    elif my_hp <= 3: # Low HP
        bid_to_win = DAILY_SALARY * 0.8
    else: # Healthy HP
        # Default bid if healthy, can be adjusted later based on competition
        bid_to_win = DAILY_SALARY * 0.6

    # If there were bids yesterday, react to the highest one
    # Given WATER_REQ=13 and supply_range=[15,25], there's almost always only 1 water unit available.
    # So, we need to outbid the highest competitor.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Bid slightly above the highest previous bid, but don't exceed daily salary significantly
        bid_to_win = max(bid_to_win, min(highest_prev_bid + 2.0, DAILY_SALARY * 0.98))

    # Adjust bid based on remaining days - become more aggressive towards the end if healthy and budget allows
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 3 and my_hp > 3 and my_budget > DAILY_SALARY:
        bid_to_win = max(bid_to_win, DAILY_SALARY * 0.75) # Ensure strong bid in late game

    # Ensure the bid does not exceed my budget
    final_bid = min(my_budget, bid_to_win)
    # Ensure bid is not negative
    final_bid = max(0.0, final_bid)

    # If budget is extremely low and I'm desperate, bid almost everything to survive
    if my_budget < DAILY_SALARY * 0.5 and my_hp <= 2:
        final_bid = min(my_budget, DAILY_SALARY * 0.99) # Desperate last-ditch effort

    return float(final_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_active_opponents = len(alive_opponents)

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.65

    if my_status['hp'] <= 3:
        base_bid = DAILY_SALARY * 0.98
    elif my_status['hp'] <= 5:
        base_bid = DAILY_SALARY * 0.90
    elif my_status['no_water_days'] > 0:
        base_bid = DAILY_SALARY * 0.80
    
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] <= 5:
                base_bid = max(base_bid, highest_prev_bid + 5)
            else:
                base_bid = max(base_bid, highest_prev_bid + 2)
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            if my_status['hp'] <= 7:
                base_bid = max(base_bid, highest_prev_bid + 3)
            else:
                base_bid = max(base_bid, highest_prev_bid + 1)
        else:
            base_bid = max(base_bid, highest_prev_bid + 1)

    if day_context['supply'] <= WATER_REQ + 5:
        if my_status['hp'] <= 5:
            base_bid = max(base_bid, DAILY_SALARY * 0.85)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.70)

    final_bid = min(my_status['budget'], base_bid)
    
    if final_bid < 1.0 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], 1.0)
    
    final_bid = max(0.0, final_bid)

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

    # If no opponents remain, bid minimally to win and save budget.
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # --- Determine base bid based on my HP and general conditions ---
    base_bid = DAILY_SALARY * 0.6 # Default moderate bid

    if my_status['hp'] <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.85
    elif my_status['hp'] <= 6: # Medium HP
        base_bid = DAILY_SALARY * 0.7
    else: # Good HP
        base_bid = DAILY_SALARY * 0.55 # Slightly lower if HP is good

    # Adjust bid based on supply scarcity (water is always scarce relative to total demand)
    # With supply 15-25 and WATER_REQ 13, water is always competitive.
    # If supply is very low, increase bid slightly.
    if day_context['supply'] < WATER_REQ * 1.5: # e.g., supply < 19.5
        base_bid *= 1.08 # Increase bid by 8%
    elif day_context['supply'] < WATER_REQ * 2: # e.g., supply < 26
        base_bid *= 1.04 # Increase bid by 4%

    # --- React to opponent's previous bids (previous_trace) ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If highest opponent bid was very high, compete fiercely.
        if highest_prev_bid >= DAILY_SALARY * 0.8: # e.g., >= 120
            if my_status['hp'] <= 4: # If my HP is also low, I must outbid.
                base_bid = max(base_bid, highest_prev_bid + 5.0)
            else: # My HP is good, still compete but can be slightly less aggressive.
                base_bid = max(base_bid, highest_prev_bid * 0.95)
        # If highest opponent bid was relatively low, try to get water efficiently.
        elif highest_prev_bid < DAILY_SALARY * 0.5: # e.g., < 75
            if my_status['hp'] > 5 and my_status['budget'] > DAILY_SALARY * (EPISODE_DAYS - day_context['day']): # If doing well
                base_bid = min(base_bid, highest_prev_bid + 1.0) # Bid just above
            else: # Still need to secure water, bid slightly above.
                base_bid = max(base_bid, highest_prev_bid * 1.05)
        else: # Moderate previous bids, ensure I'm competitive.
            base_bid = max(base_bid, highest_prev_bid + 1.0)

    # --- Final bid adjustments ---
    final_bid = min(my_status['budget'], base_bid)

    # If it's the last day and I'm desperate, bid all remaining budget.
    if (EPISODE_DAYS - day_context['day']) == 0 and my_status['hp'] <= 1:
        final_bid = my_status['budget']

    # Ensure bid is always positive and at least 1.0 to participate.
    final_bid = max(1.0, final_bid)

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

    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_competitors = len(alive_opponents) + 1

    supply_units = int(current_supply // WATER_REQ)

    # 1. Survival Mode: If HP is low or no water days are accumulating, bid aggressively
    if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1:
        bid_amount = min(my_status['budget'], DAILY_SALARY * 0.95)
        if current_day == EPISODE_DAYS and my_status['hp'] <= 3:
            bid_amount = my_status['budget']
        return bid_amount

    # 2. Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # 3. Determine competition intensity and adjust bid
    is_water_scarce = num_alive_competitors > supply_units

    if is_water_scarce:
        if yesterday_bids:
            avg_bid = sum(yesterday_bids) / len(yesterday_bids)
            bid_amount = max(DAILY_SALARY * 0.7, avg_bid + 2.0)
        else:
            bid_amount = DAILY_SALARY * 0.75
    else:
        if yesterday_bids:
            avg_bid = sum(yesterday_bids) / len(yesterday_bids)
            bid_amount = max(DAILY_SALARY * 0.4, avg_bid * 0.9)
            if my_status['hp'] > 5:
                bid_amount = max(DAILY_SALARY * 0.3, avg_bid * 0.8)
        else:
            bid_amount = DAILY_SALARY * 0.5

    final_bid = min(my_status['budget'], bid_amount)

    if final_bid <= 0 and my_status['budget'] > 0:
        final_bid = 1.0
    elif my_status['budget'] <= 0:
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid a minimal amount to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    strong_opponent_ids = ["Alex", "Eric"]
    
    # Collect yesterday's bids specifically from strong opponents, as they are the main competition
    strong_yesterday_bids = []
    for opp in alive_opponents:
        if opp['agent_id'] in strong_opponent_ids:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                strong_yesterday_bids.append(prev['bid'])

    # Default bid if no strong opponent bids or if I'm healthy
    base_bid = DAILY_SALARY * 0.5

    # If my HP is low or I've missed water recently, I need water desperately, bid aggressively
    if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1:
        base_bid = DAILY_SALARY * 0.95 # Very aggressive bid

    # Adjust bid based on strong opponents' previous behavior
    if strong_yesterday_bids:
        max_strong_prev_bid = max(strong_yesterday_bids)
        
        # If strong opponents bid high, I need to match or slightly exceed
        if max_strong_prev_bid >= DAILY_SALARY * 0.8:
            # If desperate or supply is low, bid even higher
            if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1 or day_context['supply'] < 2 * WATER_REQ:
                base_bid = max(base_bid, max_strong_prev_bid + 5.0)
            else:
                base_bid = max(base_bid, max_strong_prev_bid + 2.0)
        elif max_strong_prev_bid > DAILY_SALARY * 0.3: # Moderate strong bids
            base_bid = max(base_bid, max_strong_prev_bid + 1.0)
        # If strong opponents bid very low, my base_bid (0.5*salary) should still be competitive enough

    # If no strong opponents are active or didn't bid yesterday, consider all other opponents
    elif not strong_yesterday_bids and alive_opponents:
        all_yesterday_bids = []
        for opp in alive_opponents:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                all_yesterday_bids.append(prev['bid'])
        
        if all_yesterday_bids:
            max_all_prev_bid = max(all_yesterday_bids)
            if max_all_prev_bid > DAILY_SALARY * 0.3:
                base_bid = max(base_bid, max_all_prev_bid + 1.0)
            
    # Consider current day supply scarcity
    # If supply is scarce (less than enough for two full requirements), competition is higher
    if day_context['supply'] < 2 * WATER_REQ:
        if len(alive_opponents) >= 1: # If there's competition
            base_bid = max(base_bid, DAILY_SALARY * 0.6) # Increase base bid for scarcity

    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure bid is non-negative and has a floor if I desperately need water
    if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1:
        final_bid = max(final_bid, DAILY_SALARY * 0.3) # Ensure a minimum bid if desperate
    
    # Cap bid at a reasonable amount if not desperate to avoid overspending
    if my_status['hp'] > 5 and my_status['no_water_days'] == 0:
        final_bid = min(final_bid, DAILY_SALARY * 1.1) # Cap slightly above salary if healthy
    
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    # Initial aggressive bid due to extreme scarcity and high opponent bids from last meta-round
    base_bid = DAILY_SALARY * 0.75 # e.g., 112.5

    # Adjust bid based on current HP
    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.95 # Critical HP, bid very aggressively (e.g., 142.5)
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.85 # Low HP, bid aggressively (e.g., 127.5)
    elif my_status['hp'] >= 8:
        # High HP, can afford to be slightly less aggressive, but still competitive due to scarcity
        base_bid = DAILY_SALARY * 0.70 # e.g., 105

    # Adjust bid based on day number (late game pressure)
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days
        base_bid = max(base_bid, DAILY_SALARY * 0.90) # Ensure high bid for survival

    # Analyze opponents' previous bids from yesterday's trace
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    successful_prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        # Only consider successful bids from yesterday to infer competitive price
        if prev and prev.get('bid') is not None and prev.get('status') == 'success':
            successful_prev_bids.append(prev['bid'])

    if successful_prev_bids:
        highest_prev_bid = max(successful_prev_bids)
        
        # React to the highest successful bid from yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.8: # If opponents were aggressive yesterday
            if my_status['hp'] > 5: # If my HP is good, try to outbid smartly
                base_bid = max(base_bid, highest_prev_bid + 5)
            else: # If my HP is low, must secure water at a higher premium
                base_bid = max(base_bid, highest_prev_bid + 10)
        else: # If highest successful bid was not extremely aggressive
            if my_status['hp'] <= 3: # If my HP is low, still need to be strong
                base_bid = max(base_bid, highest_prev_bid + 5)
            else: # My HP is good, try to win with a slight edge to save budget
                base_bid = max(base_bid, highest_prev_bid + 1)

    # Ensure bid does not exceed available budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure bid is at least 1.0 to be a valid bid
    return max(1.0, final_bid)
"""
