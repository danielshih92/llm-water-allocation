# ============================================================
# Experiment: exp_079
# Agent: Cindy
# Source: exp_079
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

    # Prioritize survival if HP is low
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # If no opponents, bid low to save money (but still ensure water if possible)
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Normal play: good HP, opponents present
    current_supply = day_context['supply']

    # Estimate total water demand including myself
    total_estimated_water_demand = WATER_REQ * (num_alive_opponents + 1)

    # Adjust bid based on supply tightness
    if current_supply < total_estimated_water_demand * 1.2: # If supply is less than 1.2x of total demand, consider it tight
        bid = DAILY_SALARY * 0.7 # Bid moderately high
    else:
        bid = DAILY_SALARY * 0.5 # Ample supply, bid moderately

    # Ensure bid is at least our water requirement cost or a minimum effective bid
    bid = max(bid, WATER_REQ)

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

    days_remaining = EPISODE_DAYS - day_context['day']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    strong_opp_yesterday_bids = [] 
    
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            if opp['agent_id'] == 'Alex' or opp['agent_id'] == 'Eric': # Strong opponents from meta-round context
                strong_opp_yesterday_bids.append(prev['bid'])

    # Determine a competitive base bid
    # Given only 1 unit of water (supply_range 15-25, WATER_REQ 13), bids need to be high to win.
    competitive_bid_floor = DAILY_SALARY * 0.6 

    base_bid = DAILY_SALARY * 0.5 # Default if no info

    if strong_opp_yesterday_bids:
        max_strong_bid = max(strong_opp_yesterday_bids)
        # Try to outbid strong opponents if their bid was not excessively high
        if max_strong_bid < DAILY_SALARY * 0.9: 
            base_bid = max_strong_bid + (DAILY_SALARY * 0.05)
        else: # If they bid very high, just match or slightly below (if not desperate)
            base_bid = max_strong_bid 
    elif yesterday_bids: # Only weak opponents bid or no strong bids yesterday
        base_bid = max(yesterday_bids) + (DAILY_SALARY * 0.05)
    
    # Ensure base_bid is at least the competitive floor
    base_bid = max(base_bid, competitive_bid_floor)

    final_bid = base_bid

    # Adjust bid based on my HP and day
    if my_status['hp'] <= 2: # Critical HP: MUST win
        final_bid = DAILY_SALARY * 0.98 # Bid very high
    elif my_status['hp'] <= 5: # Low HP: Need water, be aggressive
        final_bid = max(final_bid, DAILY_SALARY * 0.85)
        # If strong opponents were very aggressive, try to outbid them
        if strong_opp_yesterday_bids and max(strong_opp_yesterday_bids) >= DAILY_SALARY * 0.8:
            final_bid = max(final_bid, max(strong_opp_yesterday_bids) + 5)
    elif my_status['hp'] >= 8 and day_context['day'] < EPISODE_DAYS / 2: # Good HP, early days: Conserve
        # If strong opponents are bidding very high, let them win to drain their budget
        if strong_opp_yesterday_bids and max(strong_opp_yesterday_bids) >= DAILY_SALARY * 0.9:
            final_bid = DAILY_SALARY * 0.3 # Significantly lower, try to get water cheaply or pass
        else:
            final_bid = max(final_bid * 0.75, DAILY_SALARY * 0.5) # Moderate conservation
    else: # Normal HP, or good HP in later days: Be competitive
        final_bid = max(final_bid, DAILY_SALARY * 0.75)
        if day_context['day'] >= EPISODE_DAYS * 0.7: # Last few days, increase aggression
            final_bid = max(final_bid, DAILY_SALARY * 0.9) # Be more aggressive towards the end

    # Final check to not bid more than budget and ensure minimum bid
    return max(0.01, min(final_bid, my_status['budget']))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 

    current_bid = DAILY_SALARY * 0.7 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if my_status['hp'] <= 2:
        current_bid = max(current_bid, DAILY_SALARY * 0.95)
    elif my_status['hp'] == 3:
        current_bid = max(current_bid, DAILY_SALARY * 0.85)
    elif my_status['hp'] == 4:
        current_bid = max(current_bid, DAILY_SALARY * 0.75)

    if my_status['no_water_days'] > 0:
        current_bid = max(current_bid, DAILY_SALARY * 0.8)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.7:
            current_bid = max(current_bid, highest_prev_bid + 5)
        elif highest_prev_bid > current_bid - 20:
             current_bid = max(current_bid, highest_prev_bid + 2)

    day = day_context['day']
    if day >= EPISODE_DAYS - 2:
        current_bid = max(current_bid, DAILY_SALARY * 0.9)
    elif day >= EPISODE_DAYS - 4:
        current_bid = max(current_bid, DAILY_SALARY * 0.8)

    final_bid = min(my_status['budget'], current_bid)

    if final_bid < DAILY_SALARY * 0.1 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.1)

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

    # If no opponents, bid minimally to save budget, but ensure survival
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4) # A safe low bid

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid strategy
    # Default bid is moderate
    bid_amount = DAILY_SALARY * 0.55

    # Adjust based on my HP
    if my_status['hp'] <= 2: # Very critical HP
        bid_amount = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Critical HP
        bid_amount = DAILY_SALARY * 0.85
    elif my_status['hp'] <= 6: # Low HP
        bid_amount = DAILY_SALARY * 0.75

    # Adjust based on supply
    num_potential_buyers = len(alive_opponents) + 1 # Including myself

    # If supply is very high, we can afford to bid less
    if day_context['supply'] >= num_potential_buyers * WATER_REQ * 1.5: # Plenty of water
        if my_status['hp'] > 4: # Only if not critical
            bid_amount = min(bid_amount, DAILY_SALARY * 0.4)
    # If supply is tight, we might need to bid more
    elif day_context['supply'] <= num_potential_buyers * WATER_REQ * 0.8: # Tight supply
        bid_amount = max(bid_amount, DAILY_SALARY * 0.65)


    # Adjust based on yesterday's opponent bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents were very aggressive
            if my_status['hp'] > 4: # If not critical, try to outbid but don't overpay too much
                bid_amount = max(bid_amount, highest_prev_bid * 0.95) # Slightly undercut or match
            else: # If critical, match or exceed
                bid_amount = max(bid_amount, highest_prev_bid + 1.0)
        elif average_prev_bid < DAILY_SALARY * 0.4: # Opponents were very conservative
            if my_status['hp'] > 6: # If not low HP, try to save money
                bid_amount = min(bid_amount, average_prev_bid * 1.2) # Bid slightly above their average
            else: # If HP is low, still need to secure water
                bid_amount = max(bid_amount, DAILY_SALARY * 0.5) # Maintain a reasonable bid

    # End game pressure
    if day_context['day'] >= EPISODE_DAYS - 2: # Last two days
        if my_status['hp'] <= 6: # If HP is not great, be more aggressive
            bid_amount = max(bid_amount, DAILY_SALARY * 0.9)
        else: # If HP is good, still be competitive
            bid_amount = max(bid_amount, DAILY_SALARY * 0.7)


    # Ensure bid is within budget and positive
    final_bid = min(my_status['budget'], max(1.0, bid_amount))

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
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

    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0

    current_bid = DAILY_SALARY * 0.6

    if my_status['hp'] <= 2:
        current_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] == 3:
        current_bid = DAILY_SALARY * 0.8

    if max_prev_bid > DAILY_SALARY * 0.8:
        current_bid = max(current_bid, max_prev_bid + 10)
    elif max_prev_bid > DAILY_SALARY * 0.5:
        current_bid = max(current_bid, max_prev_bid + 2)

    num_water_slots = int(day_context['supply'] // WATER_REQ)

    if num_water_slots == 1:
        current_bid = max(current_bid, DAILY_SALARY * 0.75)
    elif num_water_slots >= 2:
        current_bid = max(current_bid, DAILY_SALARY * 0.55)
    
    final_bid = min(my_status['budget'], current_bid)
    
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid calculation
    # Start with a moderate bid, considering my daily salary
    bid = DAILY_SALARY * 0.6 # Base 90.0

    # Adjust bid based on the current supply level
    # Higher supply means potentially less competition per unit of water
    # Lower supply means more intense competition
    supply_level = day_context['supply']
    if supply_level <= MIN_SUPPLY + 3: # Very low supply (15-18)
        bid *= 1.15 # Increase bid significantly
    elif supply_level >= MAX_SUPPLY - 3: # High supply (22-25)
        bid *= 0.9 # Decrease bid slightly
    # For medium supply, bid remains DAILY_SALARY * 0.6

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Adjust bid based on opponent's highest bid from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If the highest bid was very aggressive, I might need to match or slightly exceed
        if highest_prev_bid >= DAILY_SALARY * 0.9: # e.g., 135
            bid = max(bid, highest_prev_bid + 5) # Try to outbid
            # Cap the bid to avoid overspending excessively, but remain competitive
            bid = min(bid, DAILY_SALARY * 1.15) # Max 172.5
        elif highest_prev_bid >= DAILY_SALARY * 0.7: # e.g., 105
            bid = max(bid, highest_prev_bid + 2) # Slightly outbid
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # e.g., 75
            bid = max(bid, highest_prev_bid + 1) # Gently outbid

    # Critical adjustment: if I'm low on HP or missed water yesterday, bid very aggressively
    if my_status['no_water_days'] >= 1: # Missed water yesterday
        bid = max(bid, DAILY_SALARY * 0.85) # 127.5
    if my_status['hp'] <= 2: # Very low HP, desperate
        bid = max(bid, DAILY_SALARY * 0.98) # 147.0
    elif my_status['hp'] <= 4: # Low HP
        bid = max(bid, DAILY_SALARY * 0.8) # 120.0

    # Consider end-game strategy if near the end of the episode
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] <= 5: # Last 2 days, and HP is not great
        bid = max(bid, DAILY_SALARY * 1.0) # Bid full salary if needed to survive

    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], bid)

    # Ensure a minimal positive bid if budget allows, to stay in the game
    if final_bid < DAILY_SALARY * 0.1 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.1) # 15.0

    # Ensure bid is non-negative
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

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > int(EPISODE_DAYS / 3):
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        
        return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))

    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    elif my_status['hp'] <= int(EPISODE_DAYS / 2):
        return min(my_status['budget'], DAILY_SALARY * 0.7)
    else:
        return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQUIREMENT = 13
    MY_DAILY_SALARY = 150
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Default bid (conservative)
    bid = MY_DAILY_SALARY * 0.55 # 82.5

    # If no active opponents, bid very low to save budget
    if not alive_opponents:
        return min(my_status['budget'], MY_DAILY_SALARY * 0.3) # 45

    # Adjust bid based on my health (HP)
    if my_status['hp'] <= 2:
        bid = MY_DAILY_SALARY * 0.95 # Critical HP, bid very aggressively (142.5)
    elif my_status['hp'] <= 5:
        bid = MY_DAILY_SALARY * 0.85 # Low HP, bid aggressively (127.5)
    else:
        # Healthy, adjust based on day progression
        remaining_days = EPISODE_DAYS - day_context['day']
        if remaining_days <= 3: # Last few days, secure water
            bid = MY_DAILY_SALARY * 0.75 # 112.5
        elif remaining_days <= 6: # Mid-game
            bid = MY_DAILY_SALARY * 0.65 # 97.5
        else: # Early game
            bid = MY_DAILY_SALARY * 0.55 # 82.5

    # Analyze opponents' previous bids to inform current bid
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were bidding high, increase my bid to compete
        if highest_prev_bid > MY_DAILY_SALARY * 0.6: # If opponents bid above 90
            bid = max(bid, highest_prev_bid + 5) # Try to outbid by a small margin
        # If opponents were bidding very low and I'm healthy, I can save money
        elif highest_prev_bid < MY_DAILY_SALARY * 0.4 and my_status['hp'] > 5:
            bid = min(bid, MY_DAILY_SALARY * 0.5) # Bid 75 to be safe but save

    # Adjust bid based on supply scarcity
    # Supply range [15, 25]. My water requirement is 13.
    # If supply is low (e.g., 15-17), competition is intense.
    if day_context['supply'] <= 17:
        bid = max(bid, MY_DAILY_SALARY * 0.9) # Very aggressive for low supply (135)
    elif day_context['supply'] >= 23:
        # If supply is abundant, reduce bid if not critical and current bid is high
        if my_status['hp'] > 5 and bid > MY_DAILY_SALARY * 0.7:
            bid = min(bid, MY_DAILY_SALARY * 0.7) # Cap at 105 for high supply if healthy

    # Final bid must not exceed current budget
    final_bid = min(my_status['budget'], bid)

    # Emergency bid: If HP is critically low, bid almost all budget to survive
    if my_status['hp'] <= 1 and my_status['budget'] > 0:
        final_bid = max(1.0, my_status['budget']) # Bid whatever is left

    # Ensure bid is at least 0.0
    if final_bid < 0:
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

    # Emergency bid if HP is critically low
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                yesterday_bids.append(prev_trace['bid'])

    # Determine target bid
    # Base bid, competitive with successful opponents like Alex and Eric
    base_competitive_bid = DAILY_SALARY * 0.77  # ~115.5
    
    target_bid = base_competitive_bid

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        # If opponents bid high, ensure we outbid them with a small buffer
        # Otherwise, maintain a competitive bid but don't overspend unnecessarily
        if max_prev_bid >= DAILY_SALARY * 0.7:
            target_bid = max_prev_bid + 5.0
        else:
            target_bid = max(base_competitive_bid, max_prev_bid + 1.0)

    # Adjust bid for budget constraint
    final_bid = min(my_status['budget'], target_bid)

    # Ensure bid is not negative or zero if budget is very low
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQ = 13
    MY_DAILY_SALARY = 150
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        # If no one left, bid minimally to secure water, as per example's structure.
        return min(my_status['budget'], MY_DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Critical HP: Bid very aggressively to survive.
    if my_status['hp'] <= 2:
        return min(my_status['budget'], MY_DAILY_SALARY * 0.95)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If highest bid was very high, react based on my HP.
        if highest_prev_bid >= MY_DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # Good HP, can afford to be slightly less aggressive
                return min(my_status['budget'], MY_DAILY_SALARY * 0.6)
            else: # HP is getting low, must compete aggressively
                return min(my_status['budget'], MY_DAILY_SALARY * 0.9)
        
        # If highest bid was moderate, try to outbid it slightly.
        return min(my_status['budget'], max(MY_DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
    
    # Default strategy if no strong signals from yesterday or if HP is slightly low.
    if my_status['hp'] <= 5:
        return min(my_status['budget'], MY_DAILY_SALARY * 0.75) # Moderately aggressive
    
    # Otherwise, good HP, no strong signals, bid moderately.
    return min(my_status['budget'], MY_DAILY_SALARY * 0.55)
"""
