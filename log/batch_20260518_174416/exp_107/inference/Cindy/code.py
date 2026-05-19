# ============================================================
# Experiment: exp_107
# Agent: Cindy
# Source: exp_107
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
    num_alive_agents = len(alive_opponents) + 1 # Including myself

    # Base bid - a safe amount to try and get water
    bid = DAILY_SALARY * 0.4

    # Adjust bid based on my health (HP)
    if my_status['hp'] <= 2: # Very critical HP
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP
        bid = DAILY_SALARY * 0.75
    elif my_status['no_water_days'] > 0: # Had no water recently, but HP not critical
        bid = max(bid, DAILY_SALARY * 0.6)

    # Adjust bid based on supply scarcity
    current_supply = day_context['supply']
    # If supply is very low, competition will be fierce
    if current_supply < WATER_REQ * 1.5: # Less than enough for 1.5 agents
        if my_status['hp'] <= 4: # If desperate, bid very high
            bid = max(bid, DAILY_SALARY * 0.9)
        else: # If not desperate, but supply is low, bid higher than base
            bid = max(bid, DAILY_SALARY * 0.65)
    elif current_supply < WATER_REQ * num_alive_agents: # Supply is less than total needed
        # Competition is still high, but not as extreme as above
        bid = max(bid, DAILY_SALARY * 0.55)

    # Analyze opponent's previous bids to gauge competition
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents bid high yesterday, we might need to match or slightly exceed
        # Especially if supply is tight or I need water
        if max_yesterday_bid >= DAILY_SALARY * 0.6: # Opponents were aggressive
            if my_status['hp'] <= 4 or current_supply < WATER_REQ * 1.5: # If desperate or supply very low
                bid = max(bid, max_yesterday_bid + 5) # Try to outbid them
            else:
                bid = max(bid, avg_yesterday_bid * 1.1) # Otherwise, be competitive
        elif avg_yesterday_bid >= DAILY_SALARY * 0.4: # Opponents were moderately aggressive
             bid = max(bid, avg_yesterday_bid * 1.05)

    # Ensure bid doesn't exceed budget or is not negative
    final_bid = min(my_status['budget'], max(0.0, bid))

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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Determine base bid aggressiveness based on my status
    if my_no_water_days >= 2 or my_hp <= 2: # Critical condition: Will die soon without water
        bid_aggressiveness = 0.95 # Very aggressive
    elif my_no_water_days == 1: # Missed water yesterday: Need water but not critical yet
        bid_aggressiveness = 0.75 # Aggressive
    else: # Got water yesterday or not critical, can be more strategic
        bid_aggressiveness = 0.6 # Moderate to high, given the competitive water supply

    # Adjust aggressiveness for end game
    if current_day >= int(EPISODE_DAYS * 0.7): # Day 7 onwards
        bid_aggressiveness = max(bid_aggressiveness, 0.8) # Increase pressure

    current_bid = DAILY_SALARY * bid_aggressiveness

    # Adapt to opponent's previous bids
    highest_prev_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])
    
    if highest_prev_bid > 0: # If there was a significant bid yesterday from an opponent
        if my_no_water_days >= 2 or my_hp <= 2: # Critical
            current_bid = max(current_bid, highest_prev_bid + 15)
        elif my_no_water_days == 1: # Need water
            current_bid = max(current_bid, highest_prev_bid + 10)
        else: # Comfortable
            current_bid = max(current_bid, highest_prev_bid + 5)
    
    # Ensure bid does not exceed budget
    final_bid = min(my_budget, current_bid)

    # If budget is very low but I'm desperate, bid all I have
    if final_bid < DAILY_SALARY * 0.2 and (my_no_water_days >= 1 or my_hp <= 3):
        final_bid = my_budget

    # Bid at least 1.0 to participate if budget allows
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid - a moderate value
    bid_amount = DAILY_SALARY * 0.5

    # Prioritize survival: If HP is very low or about to lose HP
    if my_hp <= 2 or my_no_water_days >= 1:
        bid_amount = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP, still aggressive
        bid_amount = DAILY_SALARY * 0.8

    # End-game pressure: Bid more aggressively towards the end
    if current_day >= EPISODE_DAYS - 2:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.98)
    elif current_day >= EPISODE_DAYS - 4:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.75)

    # Analyze opponent's previous bids (yesterday's trace)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were bidding high, we need to be competitive
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            bid_amount = max(bid_amount, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            bid_amount = max(bid_amount, highest_prev_bid + 2)
        # If I'm healthy and opponents bid very low, try to save
        elif my_hp > 5 and highest_prev_bid < DAILY_SALARY * 0.3:
            bid_amount = min(bid_amount, highest_prev_bid * 1.2)
    
    # Minor adjustment for very abundant supply if not in critical state
    if my_hp > 4 and supply >= WATER_REQ * 2:
        bid_amount = min(bid_amount, DAILY_SALARY * 0.4)

    # Ensure bid does not exceed budget and is non-negative
    final_bid = min(my_budget, max(0.0, bid_amount))

    # Final check for absolute survival if budget is low but some bid is possible
    if (my_hp <= 2 or my_no_water_days >= 1) and my_budget > 0:
        final_bid = max(final_bid, min(my_budget, DAILY_SALARY * 0.99)) # Bid almost all budget for survival

    return final_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                # Healthy, but opponents are aggressive. Bid competitively but try to save.
                # Increased from 0.3 in example to 0.6 to be more competitive given meta-round context
                return min(my_status['budget'], DAILY_SALARY * 0.6)
            else:
                # Low HP, must bid high to survive.
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else:
            # Moderate or low bidding by opponents yesterday.
            # Bid slightly above previous high, but at least 50% of salary.
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
    else:
        # No previous bids available (e.g., first day of meta-round or opponents have no trace)
        if my_status['hp'] <= 2:
            # Critical HP, bid high to survive.
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        else:
            # Healthy, bid moderately.
            return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']

    alive_opponents = [o for o_id, o in opponents_status.items() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Phase 1: Survival Bidding - If HP is very low or I've missed water recently, bid aggressively.
    if my_current_hp <= 3 or my_no_water_days > 0:
        remaining_days = EPISODE_DAYS - current_day
        if remaining_days <= 2: # Last couple of days, go all in if needed
            return min(my_current_budget, DAILY_SALARY * 1.0) # Bid full salary
        return min(my_current_budget, DAILY_SALARY * 0.95) # High bid (142.5)

    # Phase 2: Strategic Bidding based on Opponents
    if num_alive_opponents == 0:
        # No opponents, bid minimum to get water (nominal bid, 15.0)
        return min(my_current_budget, DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])
    
    base_bid = DAILY_SALARY * 0.5 # Default moderate bid (75.0)
    target_bid = base_bid # Initialize target bid
    
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

        # Adjust bid based on opponent pressure from yesterday
        if max_yesterday_bid >= DAILY_SALARY * 0.8: # e.g., 120.0
            target_bid = max_yesterday_bid + (DAILY_SALARY * 0.05) # Bid slightly above max (e.g. +7.5)
        elif max_yesterday_bid >= DAILY_SALARY * 0.6: # e.g., 90.0
            target_bid = max_yesterday_bid + (DAILY_SALARY * 0.03) # Bid slightly above max (e.g. +4.5)
        else: # Opponents were relatively conservative
            target_bid = max(base_bid, max_yesterday_bid + 1.0)
            
        # If I have high HP, I might take a risk and bid lower to save budget in early/mid game
        if my_current_hp >= 8 and current_day < EPISODE_DAYS / 2:
            if target_bid > DAILY_SALARY * 0.75: # If calculated target bid is very high (e.g. > 112.5)
                target_bid = DAILY_SALARY * 0.7 # Cap it to save budget (105.0)
            
    else:
        # No previous bids (e.g., Day 1). Bid moderately.
        target_bid = base_bid + (DAILY_SALARY * 0.05) # 82.5

    # Ensure bid does not exceed budget
    return min(my_current_budget, target_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Look at yesterday's bids from all alive opponents
    yesterday_bids = []
    eric_is_alive = False
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            if opp_id == "Eric":
                eric_is_alive = True
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                yesterday_bids.append(prev_trace['bid'])

    # Determine base bid
    base_bid = DAILY_SALARY * 0.6 # Default if no strong signals (e.g., 90)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If the highest previous bid was from Eric or generally high, outbid it.
        # Eric's historical average is 126.0 from the meta-round context.
        if highest_prev_bid >= DAILY_SALARY * 0.8: # If highest bid was 120 or more
            base_bid = highest_prev_bid + 1.0
        else:
            # Highest bid was not that high, but Eric might be playing conservatively
            # or it's day 1. If Eric is alive, assume his historical high.
            if eric_is_alive:
                base_bid = max(base_bid, 126.0 + 1.0) # Ensure we cover Eric's known high
            else:
                base_bid = max(base_bid, highest_prev_bid + 1.0) # Outbid others

    elif eric_is_alive:
        # No bids from yesterday (e.g., Day 1), but Eric is alive. Assume his historical high.
        base_bid = 126.0 + 1.0

    # Adjust bid based on my HP
    my_bid = base_bid
    if my_status['hp'] <= 2: # Critical HP
        my_bid = max(my_bid, DAILY_SALARY * 0.95) # Bid very high (142.5)
    elif my_status['hp'] <= 4: # Low HP
        my_bid = max(my_bid, DAILY_SALARY * 0.88) # Bid high (132)

    # Consider remaining days - be more aggressive at the end if I have budget
    days_remaining = EPISODE_DAYS - day_context['day']
    if days_remaining <= 2 and my_status['budget'] >= DAILY_SALARY * 2:
        my_bid = max(my_bid, DAILY_SALARY * 0.98) # Very aggressive (147)

    # Ensure bid doesn't exceed budget
    my_bid = min(my_status['budget'], my_bid)

    # Ensure a minimum bid to stay in the game, if budget allows
    my_bid = max(my_bid, DAILY_SALARY * 0.1) # Minimum 15, to avoid 0 bids unless broke

    return my_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimally to secure water.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid strategy
    # Default bid is a good portion of salary, assuming competition
    bid = DAILY_SALARY * 0.7

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP, must win
        bid = DAILY_SALARY * 0.98
    elif my_status['hp'] <= 5: # Low HP, need water
        bid = DAILY_SALARY * 0.85
    # If HP is high ( > 5), bid remains 0.7 * DAILY_SALARY initially

    # Adjust bid based on supply: tighter supply means more competition
    current_supply = day_context['supply']
    if current_supply <= MIN_SUPPLY + 2: # Very low supply (15-17)
        bid = max(bid, DAILY_SALARY * 0.8) # Ensure high bid
    elif current_supply <= MAX_SUPPLY - 5: # Medium supply (18-20)
        bid = max(bid, DAILY_SALARY * 0.75)

    # Adjust bid based on opponents' previous bids (if available)
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If highest previous bid was very high, we need to be very competitive
        if highest_prev_bid >= DAILY_SALARY * 0.9: # e.g., Alex bidding 135-150
            if my_status['hp'] > 5: # Healthy, can be slightly strategic
                # Bid just above them, but cap at daily salary for sustainability
                bid = max(bid, highest_prev_bid + 1)
                bid = min(bid, DAILY_SALARY) # Cap at daily salary, relying on C > A for tie-break if needed
            else: # Low HP, must win, match or slightly exceed max possible
                bid = max(bid, highest_prev_bid + 5, DAILY_SALARY * 0.99)
        elif highest_prev_bid >= DAILY_SALARY * 0.7: # Moderately high bids (e.g., David)
            bid = max(bid, highest_prev_bid + 1)
        # If bids were lower, our initial bid (adjusted by HP/supply) should be fine.

    # Ensure the bid doesn't exceed current budget
    final_bid = min(my_status['budget'], bid)

    # Final check for critical HP: if my HP is very low, I will bid almost my entire salary if budget allows.
    if my_status['hp'] <= 1: # Extremely critical HP
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.99)

    # Ensure bid is not negative or zero if I have budget and need water.
    if final_bid <= 0 and my_status['budget'] > 0: 
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.05) # A very low but positive bid

    return float(max(0, final_bid))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    my_current_bid = 0.0

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        # If no opponents, bid a small amount to get water for free
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    days_left = EPISODE_DAYS - day_context['day']

    # Critical state: must get water
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        my_current_bid = DAILY_SALARY * 0.95 # Bid very high
        if highest_prev_bid > 0:
            my_current_bid = max(my_current_bid, highest_prev_bid + 5.0)
    # Low HP, need water but can be slightly less aggressive if opponents are weak
    elif my_status['hp'] <= 4:
        my_current_bid = DAILY_SALARY * 0.8
        if highest_prev_bid > 0:
            my_current_bid = max(my_current_bid, highest_prev_bid + 2.0)
    # Moderate to high HP
    else:
        if highest_prev_bid > DAILY_SALARY * 0.8:
            # Opponents are bidding very high, need to compete
            my_current_bid = highest_prev_bid + 1.0
        elif highest_prev_bid > DAILY_SALARY * 0.6:
            # Opponents are bidding moderately high
            my_current_bid = max(DAILY_SALARY * 0.7, highest_prev_bid + 1.0)
        else:
            # Opponents are bidding low or no recent high bids
            my_current_bid = DAILY_SALARY * 0.6
            if highest_prev_bid > 0:
                my_current_bid = max(my_current_bid, highest_prev_bid + 1.0)

    # Add a small buffer if budget allows and it's not too late in the game to outbid someone
    if my_status['budget'] > my_current_bid + 5.0 and days_left > 2:
        my_current_bid += 1.0

    # Ensure bid does not exceed budget and is not negative
    final_bid = min(my_status['budget'], my_current_bid)
    final_bid = max(0.0, final_bid)

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid: aim to secure water but also save some budget.
    # Given the competitive scenario (supply 15-25, my req 13), a moderately high bid is necessary.
    bid = DAILY_SALARY * 0.8 # Start with 120.0

    # Adjust bid if HP is low
    if my_status['hp'] <= 2: # Very critical HP
        bid = DAILY_SALARY * 0.95 # Bid almost all salary (142.5)
    elif my_status['hp'] <= 4: # Getting low HP
        bid = DAILY_SALARY * 0.85 # Bid high (127.5)

    # Analyze opponent's previous bids to adapt
    highest_prev_bid = 0.0
    found_prev_bid = False
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                highest_prev_bid = max(highest_prev_bid, prev['bid'])
                found_prev_bid = True
    
    if found_prev_bid:
        # If opponents are bidding high, I need to bid higher
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents are very aggressive
            bid = max(bid, highest_prev_bid + 5.0) # Bid slightly above
        elif highest_prev_bid > DAILY_SALARY * 0.5: # Opponents are moderately aggressive
            bid = max(bid, highest_prev_bid + 2.0)
        else: # Opponents are bidding low or it's early days and they are testing
            # If supply is tight, still bid competitively
            total_opponent_water_demand = sum(o['water_requirement'] for o in alive_opponents)
            remaining_supply_for_others = day_context['supply'] - WATER_REQ
            if remaining_supply_for_others < total_opponent_water_demand: # High competition for remaining water
                 bid = max(bid, highest_prev_bid + 1.0)
            else: # Less competition, can try to save
                 bid = max(bid, DAILY_SALARY * 0.7) # Try to save, but ensure it's not too low (105.0)

    # Consider the day of the meta-round
    days_left = EPISODE_DAYS - day_context['day']
    if days_left <= 2: # Last couple of days, be more aggressive if budget allows
        if my_status['budget'] > DAILY_SALARY * 1.5: # Have some buffer
            bid = max(bid, DAILY_SALARY * 0.9)
        elif my_status['budget'] < DAILY_SALARY: # Low budget, need to be careful but still try to win
            bid = max(bid, DAILY_SALARY * 0.7)

    # Ensure bid doesn't exceed budget
    bid = min(bid, my_status['budget'])

    # Ensure bid is at least a minimal amount to try and get water, unless budget is truly zero
    if my_status['budget'] > 0:
        bid = max(bid, 1.0) 

    return float(bid)
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

    # Always ensure bid does not exceed budget
    max_affordable_bid = my_status['budget']

    # Identify alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to secure water
    if not alive_opponents:
        return min(max_affordable_bid, DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                yesterday_bids.append(prev_trace['bid'])

    # Determine bid based on my HP and opponent's previous bids
    bid_amount = DAILY_SALARY * 0.5 # Default moderate bid

    if my_status['hp'] <= 2: # Critical HP, must get water
        bid_amount = DAILY_SALARY * 0.95
    elif my_status['hp'] == 3: # Low HP, high priority
        bid_amount = DAILY_SALARY * 0.8
    else: # Healthy HP
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            # If highest opponent bid was very high, react
            if highest_prev_bid >= DAILY_SALARY * 0.85:
                # If my HP is good and supply is abundant, consider backing off to save budget
                # Supply > WATER_REQ * 1.5 suggests enough for at least two agents with some leftover
                if my_status['hp'] > 5 and day_context['supply'] > WATER_REQ * 1.5:
                    bid_amount = DAILY_SALARY * 0.4 # Try to get it cheap if others overbid
                else:
                    # Otherwise, bid slightly above previous max to compete
                    bid_amount = max(DAILY_SALARY * 0.6, highest_prev_bid + 2)
            else:
                # Opponents were not bidding extremely high, slightly above their max or a good default
                bid_amount = max(DAILY_SALARY * 0.55, highest_prev_bid + 1)
        else:
            # If no yesterday_bids (e.g., first day of meta-round or all previous opponents died), use default
            bid_amount = DAILY_SALARY * 0.55 # Default moderate bid if no history

    # Ensure bid is at least a minimum sensible amount to win against low bids
    bid_amount = max(bid_amount, DAILY_SALARY * 0.15)

    return min(max_affordable_bid, bid_amount)
"""
