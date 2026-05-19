# ============================================================
# Experiment: exp_116
# Agent: Eric
# Source: exp_116
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    budget = my_status['budget']
    hp = my_status['hp']
    no_water_days = my_status['no_water_days']
    day = day_context['day']
    
    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, DAILY_SALARY * 0.9)
    elif day >= 8:
        bid = min(budget, DAILY_SALARY * 0.8)
    else:
        bid = min(budget, DAILY_SALARY * 0.6)
    
    return max(bid, 0.0)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        bid = max(0.01, min(budget, DAILY_SALARY * 0.4))
        return bid

    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    if prev_bids:
        max_prev = max(prev_bids)
        if max_prev >= DAILY_SALARY * 0.85:
            if hp > 3:
                bid = min(budget, DAILY_SALARY * 0.3)
            else:
                bid = min(budget, DAILY_SALARY * 0.95)
        else:
            target = max(DAILY_SALARY * 0.5, max_prev + 1.5)
            bid = min(budget, target)
    else:
        if hp <= 2:
            bid = min(budget, DAILY_SALARY * 0.9)
        else:
            bid = min(budget, DAILY_SALARY * 0.55)

    bid = max(0.01, bid)
    bid = min(bid, budget)
    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.3)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))

    # Base bid
    base_bid = DAILY_SALARY * 0.4

    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If someone bid very high yesterday, they might be aggressive today
        if highest_prev > DAILY_SALARY * 0.8:
            if hp > 4:
                # Save money, we can afford to lose a day
                base_bid = DAILY_SALARY * 0.25
            else:
                # Need water, bid slightly above half
                base_bid = DAILY_SALARY * 0.65
        else:
            # Outbid the highest by a small margin
            base_bid = max(base_bid, highest_prev + 2.0)
    else:
        # No yesterday data, default
        if hp <= 2:
            base_bid = DAILY_SALARY * 0.7
        else:
            base_bid = DAILY_SALARY * 0.4

    # Adjust for supply scarcity
    supply_ratio = supply / 25.0
    if supply_ratio < 0.7:
        base_bid *= 1.2
    elif supply_ratio > 0.9:
        base_bid *= 0.85

    # Ensure we don't bid more than budget
    bid = min(budget, base_bid)
    # Also ensure non-negative
    bid = max(bid, 0.0)
    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Collect last bids from previous_trace, if available
    last_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace')
        if prev and 'bid' in prev and prev['bid'] is not None:
            last_bids.append(prev['bid'])
    
    # Determine target bid
    if last_bids:
        avg_bid = sum(last_bids) / len(last_bids)
        target = avg_bid + 5.0  # small premium
    else:
        # No data: start with moderate bid
        target = DAILY_SALARY * 0.5
    
    # Adjust based on health and thirst
    if my_status['no_water_days'] > 0:
        target = max(target, DAILY_SALARY * 0.9)
    if my_status['hp'] <= 3:
        target = max(target, DAILY_SALARY * 0.8)
    
    # Ensure not more than budget
    bid = min(target, my_status['budget'])
    # Ensure at least 0
    bid = max(bid, 0.0)
    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    
    # Get yesterday's bids for alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # Determine urgency
    urgent = hp <= 2 or no_water_days >= 1
    
    # Base bid: adapt to yesterday's highest pressure
    if prev_bids:
        highest_prev = max(prev_bids)
        # Supply factor: more supply = lower competition
        if supply >= 20:
            # Can afford to be more conservative
            if urgent:
                base = min(budget, DAILY_SALARY * 0.95)
            else:
                base = min(budget, max(DAILY_SALARY * 0.45, highest_prev * 0.8))
        else:
            # Supply low, need to compete
            if urgent:
                base = min(budget, max(DAILY_SALARY * 0.95, highest_prev + 0.5))
            else:
                base = min(budget, max(DAILY_SALARY * 0.5, highest_prev + 1.0))
    else:
        # No previous data (first day or all opponents died)
        if urgent:
            base = min(budget, DAILY_SALARY * 0.9)
        elif supply >= 20:
            base = min(budget, DAILY_SALARY * 0.4)
        else:
            base = min(budget, DAILY_SALARY * 0.6)
    
    # Ensure we bid at least something and not exceed budget
    bid = max(1.0, min(budget, base))
    # Round to avoid extreme decimals
    return round(bid, 2)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Gather yesterday bids from alive opponents
    last_bids = []
    for opp in opponents_status.values():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                last_bids.append(prev['bid'])
    
    # Determine target bid based on highest last bid
    if last_bids:
        highest_last = max(last_bids)
    else:
        highest_last = 0.0
    
    # Base bid: slightly above highest last if it was aggressive, else moderate
    if highest_last > DAILY_SALARY * 0.85:  # e.g., >119
        target = highest_last + (DAILY_SALARY * 0.05)  # +7
    else:
        target = max(DAILY_SALARY * 0.4, highest_last + 1.5)
    
    # Adjust for supply: higher supply allows lower bid
    supply_ratio = supply / (25.0)  # normalized 0.6-1
    target *= supply_ratio
    
    # Adjust for HP: if low, bid more
    if hp <= 2:
        target = max(target, DAILY_SALARY * 0.7)
    elif hp <= 4:
        target = max(target, DAILY_SALARY * 0.5)
    
    # Ensure not exceed budget and reasonable max
    max_bid = min(budget, DAILY_SALARY * 1.1)
    bid = min(target, max_bid)
    return max(0.0, bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    previous_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            previous_bids.append(prev['bid'])

    # Determine urgency
    urgent = (hp <= 2) or (no_water > 0)

    if previous_bids:
        max_prev_bid = max(previous_bids)
        if urgent:
            # Need water desperately, bid above max previous but capped by budget
            target = min(budget, max_prev_bid + 1.0)
        else:
            # Healthy, try to save money by bidding slightly below max previous
            target = min(budget, max_prev_bid - 2.0)
            # But ensure we don't bid too low if supply is low
            if supply < 18:
                target = min(budget, max_prev_bid + 0.5)
    else:
        # No previous data, bid based on urgency
        if urgent:
            target = min(budget, DAILY_SALARY * 0.95)
        else:
            target = min(budget, DAILY_SALARY * 0.5)

    # Ensure minimum bid to avoid losing unnecessarily
    if target < 1.0:
        target = 1.0
    return target
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    # Constants
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Opponents alive
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Get yesterday's opponent bids from previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Average yesterday's opponent bid (if any)
    avg_opp_bid = 0.0
    if yesterday_bids:
        avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids)
    
    # Determine base bid based on supply scarcity and HP
    # If supply is low (<= 18), we need to compete; bid higher
    if supply <= 18:
        # Need to secure water: bid aggressively
        # Use avg_opp_bid + small increment, but not more than budget
        target_bid = max(DAILY_SALARY * 0.5, avg_opp_bid + 2.0)
        # If HP is very low, bid even higher
        if hp <= 2:
            target_bid = max(target_bid, DAILY_SALARY * 0.85)
        elif hp <= 4:
            target_bid = max(target_bid, DAILY_SALARY * 0.7)
    else:
        # Supply is adequate; we can be conservative
        target_bid = max(DAILY_SALARY * 0.3, avg_opp_bid - 5.0)
        # If HP low, still bid moderate to ensure water
        if hp <= 2:
            target_bid = max(target_bid, DAILY_SALARY * 0.6)
        elif hp <= 4:
            target_bid = max(target_bid, DAILY_SALARY * 0.45)
    
    # Ensure we don't exceed budget
    final_bid = min(budget, target_bid)
    # Also ensure positive bid
    final_bid = max(1.0, final_bid)
    
    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])  # ensure int
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = my_status['budget']
    no_water_days = int(my_status['no_water_days'])

    # Alive opponents
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opps)

    # Base bid: proportion of supply needed
    base = (WATER_REQ / supply) * DAILY_SALARY * 1.2  # 20% premium

    # Adjust based on HP
    if hp <= 2:
        factor = 2.0  # desperate
    elif hp <= 4:
        factor = 1.5
    elif hp <= 6:
        factor = 1.2
    else:
        factor = 1.0

    # Estimate opponent bids from previous traces or last meta-round avg
    threat_bid = 0.0
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            threat_bid = max(threat_bid, prev['bid'])
        else:
            # Fallback based on last meta-round averages (provided in context)
            # We use rough guesses: Bob ~70, Cindy ~130, David ~81
            if 'Bob' in opp['agent_id']:
                threat_bid = max(threat_bid, 70.0)
            elif 'Cindy' in opp['agent_id']:
                threat_bid = max(threat_bid, 130.0)
            elif 'David' in opp['agent_id']:
                threat_bid = max(threat_bid, 81.0)
            else:
                threat_bid = max(threat_bid, 60.0)

    # Final bid: take max of base*factor and slight edge over threat, but not exceed budget
    bid = max(base * factor, threat_bid + 2.0)
    # Cap by budget and also ensure positive
    bid = min(bid, budget)
    bid = max(bid, 0.0)
    # Return as float
    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    max_players = supply // WATER_REQ
    
    # Count alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)
    
    # Check if Cindy is alive and her previous bid
    cindy_prev_bid = None
    if 'Cindy' in opponents_status and opponents_status['Cindy']['alive']:
        trace = opponents_status['Cindy'].get('previous_trace', {})
        if trace and 'bid' in trace:
            cindy_prev_bid = trace['bid']
    
    # Base bid calculation
    if hp <= 2:
        # Need water urgently
        target_bid = DAILY_SALARY * 0.8
        if cindy_prev_bid:
            target_bid = max(target_bid, cindy_prev_bid + 2.0)
        return min(budget, target_bid)
    elif hp <= 5:
        # Moderate need, try to outbid if possible
        if cindy_prev_bid and cindy_prev_bid < DAILY_SALARY * 0.6:
            return min(budget, cindy_prev_bid + 1.0)
        else:
            return min(budget, DAILY_SALARY * 0.4)
    else:
        # High HP, conserve
        return min(budget, DAILY_SALARY * 0.1)
"""
