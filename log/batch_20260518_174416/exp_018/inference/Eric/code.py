# ============================================================
# Experiment: exp_018
# Agent: Eric
# Source: exp_018
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
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
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    else:
        highest_prev_bid = 0.0
    
    # Minimum safe bid based on my HP
    hp = my_status['hp']
    budget = my_status['budget']
    
    if hp <= 3:
        # Desperate: bid high to survive
        target_bid = max(DAILY_SALARY * 0.9, highest_prev_bid + 1.0)
        bid = min(budget, target_bid)
    else:
        # Conservative: bid just above previous highest
        target_bid = max(DAILY_SALARY * 0.4, highest_prev_bid + 0.5)
        bid = min(budget, target_bid)
    
    # Ensure non-negative
    bid = max(0.0, bid)
    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    
    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine base bid from yesterday's highest pressure
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
    else:
        highest_prev = 0
    
    # Estimate today's opponent bids: if supply low, they may bid higher
    scarcity_factor = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    estimated_opponent_bid = highest_prev * (1.0 + 0.2 * scarcity_factor)
    
    # My needed bid: enough to win if necessary
    my_need = DAILY_SALARY * 0.9  # ceiling
    if hp <= 3:
        # desperate
        target = min(budget, my_need)
    else:
        # normal: bid just above estimated opponent or a safe threshold
        if scarcity_factor > 0.6:
            # very low supply, bid high
            target = min(budget, max(DAILY_SALARY * 0.8, estimated_opponent_bid + 2.0))
        elif scarcity_factor > 0.3:
            target = min(budget, max(DAILY_SALARY * 0.6, estimated_opponent_bid + 1.0))
        else:
            # high supply, bid low
            target = min(budget, max(DAILY_SALARY * 0.3, estimated_opponent_bid * 0.8))
    
    # Ensure we don't overbid early; save budget for later
    remaining_days = 10 - day
    if remaining_days > 5 and hp > 5:
        target = min(target, DAILY_SALARY * 0.4)
    
    bid = max(0, min(budget, target))
    return int(bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    # Ensure supply is float? Convert to int for calculations.
    supply = int(supply) if not isinstance(supply, int) else supply
    day = day_context['day']
    
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    previous_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            previous_bids.append(prev['bid'])
    
    # Base bid from salary percentage
    if hp <= 3 or no_water_days > 0:
        base_bid = DAILY_SALARY * 0.8
    else:
        base_bid = DAILY_SALARY * 0.6
    
    # Adjust for low supply
    if supply <= 16:
        base_bid = min(base_bid * 1.3, DAILY_SALARY * 0.95)
    
    # Outbid yesterday's highest competitor slightly if they were strong
    if previous_bids:
        max_prev = max(previous_bids)
        # If we need water badly, outbid by a bit; otherwise stay conservative
        if hp <= 2 or no_water_days >= 2:
            base_bid = max(base_bid, max_prev + 1.5)
        else:
            # Only outbid if we can afford and if opponent's bid wasn't enormous (> salary)
            if max_prev < DAILY_SALARY * 0.9:
                base_bid = max(base_bid, max_prev + 1)
    
    # Cap bid: never more than budget, never less than 1
    final_bid = min(budget, max(1, base_bid))
    # Ensure no float index issues: not needed here, but safe
    # Also ensure bid does not exceed daily salary * 1.2 as extreme safety
    final_bid = min(final_bid, DAILY_SALARY * 1.2)
    return round(final_bid, 2)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    SALARY = 140
    supply = int(day_context['supply'])
    max_winners = int(supply // WATER_REQ)
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    n_alive = len(alive_opponents) + 1
    prev_bids = []
    for opp_id, opp in alive_opponents.items():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    if len(prev_bids) >= max_winners:
        sorted_bids = sorted(prev_bids, reverse=True)
        threshold = sorted_bids[max_winners - 1] + 5
    else:
        threshold = SALARY * 0.7
    max_bid = min(budget, SALARY * 0.95)
    if hp <= 2 or no_water_days >= 2:
        bid = min(max_bid, threshold + 10)
    elif hp <= 4:
        bid = min(max_bid, threshold + 5)
    else:
        bid = min(max_bid, max(SALARY * 0.5, threshold - 2))
    bid = max(bid, 1.0)
    bid = min(bid, budget)
    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    # Get current day and supply
    day = int(day_context['day'])
    supply = int(day_context['supply'])
    
    # Identify alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Get yesterday's max bid from alive opponents (using previous_trace)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid calculation
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
    else:
        max_yesterday = 0.0
    
    # Adjust based on supply scarcity
    supply_factor = 1.0
    if supply < 20:
        supply_factor = 1.2
    
    # Determine our bid
    if my_status['hp'] <= 2:
        # Desperate: bid high to ensure water
        target_bid = DAILY_SALARY * 0.9 * supply_factor
    else:
        # Normal: base bid on yesterday's competition
        if max_yesterday >= DAILY_SALARY * 0.7:
            # High competition, be cautious if we have good HP, else match
            if my_status['hp'] > 5:
                target_bid = DAILY_SALARY * 0.4 * supply_factor
            else:
                target_bid = max(DAILY_SALARY * 0.5, max_yesterday + 2.0) * supply_factor
        else:
            # Low competition, bid moderately
            target_bid = max(DAILY_SALARY * 0.4, max_yesterday + 1.5) * supply_factor
    
    # Ensure we don't exceed budget
    bid = min(int(target_bid), my_status['budget'])
    
    # Never bid zero if we need water (no_water_days)
    if my_status['no_water_days'] >= 2:
        bid = max(bid, int(DAILY_SALARY * 0.6))
    
    # Safety: at least 1
    bid = max(bid, 1)
    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    my_hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0
    
    # Determine need:
    urgent = my_hp <= 2 or no_water_days >= 1
    
    # Supply scarcity: low supply increases competition
    supply_scarcity = supply <= 18
    
    if urgent:
        # Need water badly: bid above max previous, but not exceed budget
        target = max(DAILY_SALARY * 0.9, max_prev_bid + 2)
        # Cap at budget and a reasonable maximum
        bid = min(budget, target)
    else:
        # Not urgent: try to save
        if supply_scarcity:
            # Bidding may still be competitive
            target = max(DAILY_SALARY * 0.4, max_prev_bid * 0.8)
        else:
            target = max(DAILY_SALARY * 0.2, max_prev_bid * 0.6)
        bid = min(budget, target)
    
    # Ensure bid is at least 0
    bid = max(0, bid)
    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = {k: o for k, o in opponents_status.items() if o['alive']}
    # Baseline bid: 40% of salary, adjusted by supply scarcity
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    base_bid = DAILY_SALARY * (0.3 + 0.3 * (1 - supply_ratio))
    # Urgency based on hp and no_water_days
    if hp <= 2 or no_water_days >= 1:
        urgency = 0.9
    elif hp <= 4:
        urgency = 0.7
    else:
        urgency = 0.4
    bid = max(base_bid, DAILY_SALARY * urgency)
    # Consider yesterday's opponent bids
    if alive_opponents:
        max_prev_bid = 0.0
        for opp_id, opp in alive_opponents.items():
            prev = opp.get('previous_trace', {})
            if prev and 'bid' in prev and prev['bid'] is not None:
                if prev['bid'] > max_prev_bid:
                    max_prev_bid = prev['bid']
        if max_prev_bid > 0:
            # If someone bid very high, we may need to match or exceed for survival
            if hp <= 3:
                bid = max(bid, max_prev_bid + 2.0)
            else:
                # If we have good hp, we can be conservative
                bid = max(bid, max_prev_bid * 0.7)
    # Ensure bid not exceed budget and not negative
    bid = min(bid, budget)
    bid = max(bid, 0.0)
    # For first few days, avoid being too high to save budget
    if day <= 2 and hp > 3:
        bid = min(bid, DAILY_SALARY * 0.5)
    return bid
"""
