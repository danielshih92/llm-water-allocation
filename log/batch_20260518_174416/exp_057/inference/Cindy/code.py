# ============================================================
# Experiment: exp_057
# Agent: Cindy
# Source: exp_057
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no active opponents, bid a minimal amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid calculation - starts with a moderate percentage of salary
    base_bid = DAILY_SALARY * 0.5

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical health
        base_bid = DAILY_SALARY * 0.9
    elif my_status['hp'] == 3: # High pressure
        base_bid = DAILY_SALARY * 0.7
    else: # Comfortable health (hp >= 4)
        base_bid = DAILY_SALARY * 0.4

    # Adjust bid based on current supply
    supply = day_context['supply']
    if supply <= 18.0: # Low supply, higher competition expected
        base_bid *= 1.15
    elif supply >= 22.0: # High supply, less competition expected
        base_bid *= 0.85

    # Adjust bid based on opponent's previous day's bidding behavior
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents were very aggressive
            # Try to outbid, but ensure it's at least the calculated base_bid
            base_bid = max(base_bid, highest_prev_bid + 5.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Opponents were moderately aggressive
            base_bid = max(base_bid, highest_prev_bid + 2.0)
        else: # Opponents were conservative
            base_bid = max(base_bid, highest_prev_bid + 1.0)

    # Ensure bid doesn't exceed budget and is at least a minimal amount
    final_bid = min(my_status['budget'], max(1.0, base_bid))

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

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    num_water_slots = int(current_supply // WATER_REQ)

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    bid = 0.0

    if my_current_hp <= 2: 
        bid = DAILY_SALARY * 0.95
    elif my_current_hp <= 4: 
        bid = DAILY_SALARY * 0.85
    else: 
        bid = DAILY_SALARY * 0.6

        if yesterday_bids:
            max_prev_bid = max(yesterday_bids)
            avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

            if max_prev_bid >= DAILY_SALARY * 0.8:
                bid = max(bid, max_prev_bid + 1.0)
            elif max_prev_bid >= DAILY_SALARY * 0.5:
                bid = max(bid, avg_prev_bid * 1.1)
            else:
                bid = min(bid, max_prev_bid + 5.0)

    total_competitors = num_alive_opponents + 1
    if num_water_slots < total_competitors:
        if my_current_hp > 4:
            bid = max(bid, DAILY_SALARY * 0.75)
        if num_water_slots == 1 and total_competitors > 1:
            bid = max(bid, DAILY_SALARY * 0.9)

    if current_day >= EPISODE_DAYS - 2:
        if my_current_hp > 0:
            bid = max(bid, DAILY_SALARY * 0.9)

    final_bid = min(my_current_budget, bid)

    if my_current_hp <= 9 and my_current_budget > 0:
        final_bid = max(final_bid, 1.0)

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)
    
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    target_bid = DAILY_SALARY * 0.5 

    if yesterday_bids:
        highest_prev_opp_bid = max(yesterday_bids)
        lowest_prev_opp_bid = min(yesterday_bids)

        if highest_prev_opp_bid > DAILY_SALARY * 0.8 and my_hp > 3: 
            target_bid = DAILY_SALARY * 0.75 
        elif highest_prev_opp_bid > DAILY_SALARY * 0.4: 
            target_bid = highest_prev_opp_bid + 5 
        else: 
            target_bid = lowest_prev_opp_bid + 2 
    
    if my_hp <= 2:
        return min(my_budget, DAILY_SALARY * 1.2) 

    if current_day == EPISODE_DAYS and my_hp > 0:
        return my_budget

    supply_ratio = (current_supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_bid_multiplier = 1.1 - (supply_ratio * 0.2)
    target_bid *= supply_bid_multiplier

    final_bid = min(my_budget, target_bid)
    final_bid = max(DAILY_SALARY * 0.2, final_bid) 
    
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], 1.0) 

    base_bid = DAILY_SALARY * 0.6 

    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.95 
    elif my_status['hp'] <= 5:
        base_bid = DAILY_SALARY * 0.85 
    elif my_status['hp'] <= 8:
        base_bid = DAILY_SALARY * 0.7 

    if day_context['day'] >= EPISODE_DAYS / 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.75)
        if my_status['hp'] <= 5:
            base_bid = max(base_bid, DAILY_SALARY * 0.9)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        
        if day_context['supply'] < (WATER_REQ * (num_alive_opponents + 1)):
            if my_status['hp'] < 10: 
                base_bid = max(base_bid, max_prev_bid + 5.0) 
            else:
                base_bid = max(base_bid, max_prev_bid + 1.0) 
        else:
            if my_status['hp'] < 10:
                base_bid = max(base_bid, max_prev_bid * 1.05) 
            else:
                base_bid = min(base_bid, max(max_prev_bid * 0.9, DAILY_SALARY * 0.4)) 

    if my_status['hp'] < 10 and my_status['budget'] > 0:
        base_bid = max(base_bid, DAILY_SALARY * 0.1) 

    final_bid = min(my_status['budget'], base_bid)
    
    if final_bid == 0 and my_status['budget'] > 0 and my_status['hp'] < 10:
        final_bid = 1.0

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    current_day = day_context['day']
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_players = len(alive_opponents) + 1 # Including myself

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Start with a moderate base bid
    base_bid = DAILY_SALARY * 0.55

    # 1. Critical HP and no-water-days adjustment
    if my_hp <= 2:
        # Desperate for water, bid very high
        base_bid = DAILY_SALARY * 0.95
    elif my_no_water_days > 0:
        # Missed water yesterday, need to secure today
        base_bid = max(base_bid, DAILY_SALARY * 0.75)

    # 2. Opponent pressure adjustment based on yesterday's bids
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        # If opponents were aggressive, try to outbid them slightly
        if max_prev_bid >= DAILY_SALARY * 0.7:
            base_bid = max(base_bid, max_prev_bid + 5.0)
        elif max_prev_bid >= DAILY_SALARY * 0.5:
            base_bid = max(base_bid, max_prev_bid + 2.0)

    # 3. Supply-demand adjustment
    # Estimate total water needed by all alive players
    estimated_total_demand = num_alive_players * WATER_REQ

    if supply < estimated_total_demand * 0.8:
        # Supply is scarce, competition will be high
        base_bid = max(base_bid, DAILY_SALARY * 0.7)
    elif supply > estimated_total_demand * 1.5:
        # Supply is abundant, can afford to bid lower if not desperate
        if my_hp > 4 and my_no_water_days == 0:
            base_bid = min(base_bid, DAILY_SALARY * 0.4)

    # Ensure bid does not exceed budget
    final_bid = min(base_bid, my_budget)

    # Ensure a minimum bid if budget allows, to stay in contention
    if my_budget > 0:
        final_bid = max(final_bid, 1.0)
    else:
        final_bid = 0.0 # No budget, cannot bid

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
        # If no opponents, bid minimally to secure water and save budget
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Default bid if no previous bids or for initial turns
    base_bid = DAILY_SALARY * 0.55 # 82.5

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents are bidding very aggressively (e.g., near their daily salary)
        if highest_prev_bid >= DAILY_SALARY * 0.85: # 127.5
            if my_status['hp'] > 3: # If my HP is good, try to conserve budget
                bid_amount = DAILY_SALARY * 0.3 # 45
            else: # If my HP is low, I need water, bid very high
                bid_amount = DAILY_SALARY * 0.95 # 142.5
        # If opponents are bidding moderately
        else:
            # Bid slightly above the highest previous bid, but not less than a moderate base bid
            bid_amount = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5) # max(75, highest_prev_bid + 1.5)
    else:
        # If no previous bids (e.g., Day 1, or all previous bidders died)
        # Use the base bid, which is a moderate starting point
        bid_amount = base_bid

    # Final check for critical HP, overrides other bidding logic if very low
    if my_status['hp'] <= 2:
        bid_amount = DAILY_SALARY * 0.9 # 135

    # Ensure the bid does not exceed current budget
    final_bid = min(my_status['budget'], bid_amount)

    # Ensure the bid is positive if budget allows, to participate
    if final_bid <= 0 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], 1.0) # Bid a token amount

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
    
    # If no opponents, bid minimum to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # Determine a baseline bid if no previous bids are available (e.g., Day 1)
    base_bid_if_no_prev = DAILY_SALARY * 0.5 
    if my_status['hp'] <= 2:
        base_bid_if_no_prev = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 5:
        base_bid_if_no_prev = DAILY_SALARY * 0.7

    if not yesterday_bids:
        return min(my_status['budget'], base_bid_if_no_prev)

    highest_prev_bid = max(yesterday_bids)
    
    # Given WATER_REQ=13 and supply_range=[15,25], there's effectively always 1 slot for a full requirement.
    # Competition is always for this single slot.

    bid_amount = 0.0

    if my_status['hp'] <= 2: # Critical HP: Must get water
        # Bid very aggressively, slightly above highest previous bid, or a high percentage of salary
        bid_amount = max(highest_prev_bid * 1.05, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 5: # Low HP: Need water, but can be slightly less aggressive
        # Bid competitively, slightly above highest previous bid
        bid_amount = max(highest_prev_bid * 1.02, DAILY_SALARY * 0.8)
    else: # Healthy HP: Can be more strategic
        # Competition is always for the single slot that satisfies my_water_requirement
        if len(alive_opponents) == 1: # Only one opponent
            bid_amount = max(highest_prev_bid * 1.01, DAILY_SALARY * 0.6) # Just outbid them slightly
        else: # Multiple opponents
            bid_amount = max(highest_prev_bid * 1.01, DAILY_SALARY * 0.7) # Slight edge, but still conservative if possible

    # Ensure bid is at least a minimum value (1.0) and doesn't exceed budget
    final_bid = min(my_status['budget'], max(bid_amount, 1.0))
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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']
    current_supply = day_context['supply']

    # Default bid: a moderate bid to stay competitive but save budget
    bid = DAILY_SALARY * 0.65 

    # Identify strong opponents based on meta-round context
    # David and Alex are the strongest based on yesterday's performance
    strong_opponent_ids = ["David", "Alex"]
    
    highest_strong_opp_bid_yesterday = 0
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive'] and opp_id in strong_opponent_ids:
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                highest_strong_opp_bid_yesterday = max(highest_strong_opp_bid_yesterday, prev_trace['bid'])

    # --- Bidding logic based on urgency --- 

    # Most critical: Low HP or consecutive no-water days
    if my_hp <= 2 or my_no_water_days > 0:
        # Bid very aggressively to survive. Target to beat strong opponents.
        bid = max(DAILY_SALARY * 0.98, highest_strong_opp_bid_yesterday + 5)
    
    # High competition: Low supply
    elif int(current_supply) < WATER_REQ * 2: # Use int() for supply comparison
        # Increase bid significantly due to scarcity
        bid = max(DAILY_SALARY * 0.88, highest_strong_opp_bid_yesterday + 3)

    # Late game pressure
    elif current_day >= EPISODE_DAYS - 2: # Last 2 days
        # Be aggressive to secure survival towards the end
        bid = max(DAILY_SALARY * 0.92, highest_strong_opp_bid_yesterday + 4)
    
    # Normal conditions: Adjust based on strong opponent's last bid
    elif highest_strong_opp_bid_yesterday > 0:
        # Bid slightly above their last high bid to stay competitive
        bid = max(bid, highest_strong_opp_bid_yesterday + 1.5)
    
    # Ensure bid is at least a minimum to be competitive
    bid = max(bid, DAILY_SALARY * 0.4) 
    
    # Ensure bid does not exceed budget
    bid = min(my_budget, bid)

    return bid
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
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid conservatively to save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid = DAILY_SALARY * 0.55 # Default bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # Scenario 1: Opponents are bidding high (aggressive)
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 4: # My HP is good, can try to conserve or match
                # Try to outbid if supply is low, otherwise conserve
                if day_context['supply'] < WATER_REQ * 2: # Tight supply, be competitive
                    bid = max(highest_prev_bid + 1.0, DAILY_SALARY * 0.75)
                else: # Abundant supply, conserve
                    bid = DAILY_SALARY * 0.6
            else: # My HP is low (<= 4), must secure water
                bid = max(highest_prev_bid + 1.0, DAILY_SALARY * 0.95)
        
        # Scenario 2: Opponents are bidding moderately/low
        else:
            # Bid slightly above highest previous bid, but ensure it's at least a reasonable amount
            bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)
            # If supply is tight, increase bid
            if day_context['supply'] < WATER_REQ * 2:
                bid *= 1.05 # Increase by 5%
    
    # Override if my HP is critically low, regardless of opponent bids
    if my_status['hp'] <= 2:
        bid = max(bid, DAILY_SALARY * 0.98) # Very aggressive to survive
    elif my_status['hp'] <= 4: # Low HP, still aggressive
        bid = max(bid, DAILY_SALARY * 0.85)

    # Adjust for end game
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days
        if my_status['hp'] <= 5: # If HP is not great, bid very aggressively
            bid = max(bid, DAILY_SALARY * 0.95)
        else: # If HP is good, still ensure water to finish
            bid = max(bid, DAILY_SALARY * 0.7)

    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], bid)
    
    # Ensure a minimal bid if budget allows, to avoid zero bids unless truly out of money
    if final_bid <= 0 and my_status['budget'] > 0:
        final_bid = 0.01

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

    available_units = int(day_context['supply'] // WATER_REQ)

    strong_opponents_bids = []
    num_relevant_alive_opponents = 0
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive'] and opp_data['water_requirement'] >= 10:
            num_relevant_alive_opponents += 1
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None and prev_trace['bid'] > 0:
                strong_opponents_bids.append(prev_trace['bid'])

    base_bid = DAILY_SALARY * 0.75

    if strong_opponents_bids:
        highest_prev_bid = max(strong_opponents_bids)
        base_bid = max(base_bid, highest_prev_bid + 1)

    if available_units == 0:
        return 0.0

    if available_units == 1:
        if my_status['hp'] <= 2:
            base_bid = max(base_bid, DAILY_SALARY * 0.95)
        elif my_status['hp'] <= 4:
            base_bid = max(base_bid, DAILY_SALARY * 0.90)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.85)
    else:
        if num_relevant_alive_opponents >= available_units:
            if my_status['hp'] <= 2:
                base_bid = max(base_bid, DAILY_SALARY * 0.90)
            else:
                base_bid = max(base_bid, DAILY_SALARY * 0.80)
        else:
            if my_status['hp'] <= 2:
                base_bid = max(base_bid, DAILY_SALARY * 0.85)
            else:
                base_bid = min(base_bid, DAILY_SALARY * 0.70)

    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2:
        if my_status['hp'] <= 4:
            base_bid = max(base_bid, DAILY_SALARY * 0.95)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.85)

    final_bid = min(base_bid, my_status['budget'])

    return max(0.0, final_bid)
"""
