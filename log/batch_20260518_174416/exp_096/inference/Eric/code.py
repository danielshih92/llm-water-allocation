# ============================================================
# Experiment: exp_096
# Agent: Eric
# Source: exp_096
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MY_HP = my_status['hp']
    BUDGET = my_status['budget']
    ALIVE_OPPONENTS = [o for o in opponents_status.values() if o['alive']]
    if not ALIVE_OPPONENTS:
        return min(BUDGET, DAILY_SALARY * 0.4)
    if MY_HP <= 2:
        return min(BUDGET, DAILY_SALARY * 0.9)
    elif MY_HP <= 3:
        return min(BUDGET, DAILY_SALARY * 0.7)
    else:
        return min(BUDGET, DAILY_SALARY * 0.45)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Get yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))
    
    # Base bid calculation
    if not yesterday_bids:
        # First day or no info: conservative
        base_bid = DAILY_SALARY * 0.5
    else:
        highest_prev = max(yesterday_bids)
        # React to high pressure
        if highest_prev >= DAILY_SALARY * 0.8:
            base_bid = max(DAILY_SALARY * 0.7, highest_prev + 2.0)
        else:
            base_bid = max(DAILY_SALARY * 0.5, highest_prev + 1.5)
    
    # Adjust for personal urgency
    if hp <= 2 or no_water_days >= 1:
        urgent_bid = min(budget, DAILY_SALARY * 0.95)
        return max(urgent_bid, base_bid)
    
    # If low supply, increase bid
    if supply < 18:
        base_bid = max(base_bid, DAILY_SALARY * 0.7)
    
    # Ensure we don't exceed budget or go below minimum meaningful
    bid = min(budget, base_bid)
    bid = max(bid, 5.0)  # avoid zero bid
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
    
    # Get yesterday's max bid from alive opponents with previous trace
    max_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            if prev['bid'] > max_prev_bid:
                max_prev_bid = prev['bid']
    
    # Determine base bid
    if no_water_days > 0:
        # Dehydrated, need water urgently
        if supply < 20:
            base_bid = DAILY_SALARY * 0.95
        else:
            base_bid = DAILY_SALARY * 0.75
    elif hp <= 3:
        if supply < 20:
            base_bid = DAILY_SALARY * 0.8
        else:
            base_bid = DAILY_SALARY * 0.5
    else:
        if supply < 18:
            base_bid = DAILY_SALARY * 0.7
        elif supply < 22:
            base_bid = DAILY_SALARY * 0.45
        else:
            base_bid = DAILY_SALARY * 0.3
    
    # Adjust based on yesterday's highest bid
    if max_prev_bid > 130:
        # Cindy or Alex likely bid high again; match or slight increment
        target = min(budget, max_prev_bid + 5)
        if target > base_bid:
            base_bid = target
    elif max_prev_bid > 90:
        # Some competition
        if base_bid < max_prev_bid + 10:
            base_bid = max_prev_bid + 10
    
    # Ensure bid is at least 0 and within budget
    bid = min(budget, max(0, base_bid))
    
    return int(bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
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
        return min(budget, DAILY_SALARY * 0.4)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine target bid based on my state and yesterday's pressure
    base_bid = DAILY_SALARY * 0.6  # moderate baseline

    if hp <= 2 or no_water_days >= 2:
        # Desperate: need water
        target = min(budget, DAILY_SALARY * 0.95)
    else:
        # Comfortable: respond to competition
        if yesterday_bids:
            max_prev = max(yesterday_bids)
            # If opponents were aggressive yesterday, undercut if possible
            if max_prev >= DAILY_SALARY * 0.85:
                if hp > 4:
                    target = min(budget, DAILY_SALARY * 0.3)
                else:
                    target = min(budget, max(DAILY_SALARY * 0.5, max_prev + 2.0))
            else:
                target = min(budget, max(DAILY_SALARY * 0.5, max_prev + 1.5))
        else:
            target = min(budget, DAILY_SALARY * 0.55)

    # Adjust based on supply scarcity
    if supply < 18:
        target = max(target, DAILY_SALARY * 0.7)
    elif supply > 22:
        target = min(target, DAILY_SALARY * 0.6)

    # Ensure not exceeding budget and min 1
    final_bid = min(budget, target)
    final_bid = max(1.0, final_bid)
    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Determine if I'm desperate
    desperate = (hp <= 2) or (no_water_days >= 2)
    
    # Default bid for day 1 or when no trace
    default_bid = min(budget, DAILY_SALARY * 0.75)
    
    # Gather yesterday's bids from opponents that have trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if desperate:
            #
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Check if any opponent has previous_trace to gauge yesterday's behavior
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))
    
    # Estimate average opponent bid from yesterday, if available
    if prev_bids:
        avg_prev_bid = sum(prev_bids) / len(prev_bids)
    else:
        avg_prev_bid = DAILY_SALARY * 0.75  # default guess
    
    # Strategy: bid to win water if needed, but conserve budget
    # If supply is low and we need water, bid moderately above average
    # If supply is high, bid low
    # If we have high HP, we can afford to lose a round
    
    # Water need: if we have 0 water days, we die, so must bid high
    if no_water_days >= 2 and hp <= 2:
        target_bid = min(budget, DAILY_SALARY * 1.2)
    elif no_water_days >= 1:
        target_bid = min(budget, avg_prev_bid * 1.1 + 5)
    else:
        # Normal day: bid based on supply
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 to 1
        if supply_ratio < 0.3:
            # low supply, need to compete
            target_bid = min(budget, avg_prev_bid * 1.05 + 3)
        elif supply_ratio < 0.6:
            target_bid = min(budget, avg_prev_bid * 0.9)
        else:
            # high supply, bid low
            target_bid = min(budget, max(DAILY_SALARY * 0.3, avg_prev_bid * 0.5))
    
    # Ensure we do not exceed budget
    final_bid = max(0, min(budget, target_bid))
    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    day = day_context['day']
    budget = my_status['budget']
    hp = my_status['hp']
    
    # Number of winners possible given supply
    winners = int(supply // WATER_REQ)  # integer division
    
    # Base bid: 40% of salary
    base_bid = DAILY_SALARY * 0.4
    
    # Adjust for scarcity
    if winners == 1:
        base_bid *= 1.5
    elif winners == 2:
        base_bid *= 1.2
    # For 3 or more, keep base
    
    # Adjust for own health
    if hp <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    elif hp <= 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.6)
    
    # Look at yesterday's trace from opponents
    max_prev_bid = 0.0
    for opp_id, opp_state in opponents_status.items():
        if opp_state['alive']:
            prev = opp_state.get('previous_trace', {})
            if prev and 'bid' in prev and prev['bid'] is not None:
                if prev['bid'] > max_prev_bid:
                    max_prev_bid = prev['bid']
    
    # Raise bid to beat yesterday's highest
    if max_prev_bid > 0:
        target = max_prev_bid + 1.0
        if target > base_bid:
            base_bid = target
    
    # Cap by budget
    final_bid = min(base_bid, budget)
    # Ensure positive bid
    final_bid = max(final_bid, 1.0)
    
    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    # Constants
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        # No competition, bid minimum to get water
        return min(budget, DAILY_SALARY * 0.3)
    
    # Gather previous highest bid among alive opponents
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))
    
    # Determine target bid based on hp and opponent history
    if prev_bids:
        max_prev = max(prev_bids)
        # Opponents tend to bid high >100. We'll bid just below max_prev to save money
        if hp <= 2:
            # Desperate: outbid by small margin
            target_bid = max_prev + 1.0
        elif hp <= 5:
            # Moderate risk: bid around 70% of max_prev
            target_bid = max_prev * 0.7
        else:
            # Safe: bid 45% of max_prev
            target_bid = max_prev * 0.45
        # Also cap by budget and reasonable max
        target_bid = min(target_bid, budget)
        target_bid = max(target_bid, DAILY_SALARY * 0.2)  # never too low
        return target_bid
    else:
        # No history: default based on hp and supply
        if hp <= 2:
            bid = DAILY_SALARY * 0.9
        elif hp <= 5:
            bid = DAILY_SALARY * 0.6
        else:
            bid = DAILY_SALARY * 0.4
        return min(budget, bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid as fraction of salary depending on HP
    if hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        base_bid = DAILY_SALARY * 0.7
    elif hp <= 6:
        base_bid = DAILY_SALARY * 0.5
    else:
        base_bid = DAILY_SALARY * 0.3

    # Adjust for supply scarcity
    supply_ratio = supply / (25 + 15) * 2  # normalized roughly
    if supply < 18:
        base_bid *= 1.3
    elif supply > 22:
        base_bid *= 0.8

    # Exploit yesterday's highest bid
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        if highest_prev > DAILY_SALARY * 0.9:
            # Opponents were very aggressive, we can undercut if we have HP
            if hp > 4:
                base_bid = min(base_bid, DAILY_SALARY * 0.4)
            else:
                base_bid = max(base_bid, highest_prev * 0.85)
        elif highest_prev > DAILY_SALARY * 0.6:
            # Moderate aggression, try to match or slightly beat
            base_bid = max(base_bid, highest_prev * 0.85)
        else:
            # Low aggression, we can be economical
            base_bid = min(base_bid, DAILY_SALARY * 0.5)

    # If we have no water for too long, urgent
    if no_water_days >= 2:
        base_bid *= 1.5

    # Ensure we do not exceed budget
    final_bid = min(budget, max(0, int(base_bid)))

    # On last day, spend all but small reserve
    if day == 9:  # episode_days=10, day index 0-9? Actually day_context['day'] is 0-indexed? We assume 0 to 9
        final_bid = min(budget, final_bid)  # keep as is but ensure we don't overbid
        # Actually we might want to bid more if we need water
        if hp <= 3:
            final_bid = min(budget, DAILY_SALARY * 0.95)

    return final_bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    highest_prev_bid = max(prev_bids) if prev_bids else 0

    # Determine base bid percentage
    if hp <= 2 or no_water_days > 0:
        # desperate: need water now
        base_bid_pct = 0.9
        if highest_prev_bid > 0:
            base_bid = max(DAILY_SALARY * base_bid_pct, highest_prev_bid + 2)
        else:
            base_bid = DAILY_SALARY * base_bid_pct
    elif hp > 5:
        # healthy, conserve budget
        base_bid_pct = 0.4
        base_bid = DAILY_SALARY * base_bid_pct
    else:
        # moderate health
        base_bid_pct = 0.6
        base_bid = DAILY_SALARY * base_bid_pct

    # Adjust for low supply (more competition)
    if supply < 20:
        base_bid *= 1.1

    # Ensure not exceed budget
    bid = min(budget, base_bid)
    # Ensure non-negative
    bid = max(0, bid)
    return int(bid)
"""
