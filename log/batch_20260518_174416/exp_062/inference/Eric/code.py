# ============================================================
# Experiment: exp_062
# Agent: Eric
# Source: exp_062
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)
    
    # Extract yesterday's bids from traces
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        aggressive_threshold = DAILY_SALARY * 0.7  # ~98
        if highest_prev >= aggressive_threshold:
            # Opponent aggressive yesterday; maybe still aggressive
            if my_status['hp'] > 3:
                # Healthy, save money
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            else:
                # Desperate, need water
                return min(my_status['budget'], DAILY_SALARY * 0.9)
        else:
            # Opponent moderate; outbid slightly
            target = highest_prev + 2  # small increment
            max_bid = min(my_status['budget'], DAILY_SALARY * 0.8)
            return min(max_bid, target)
    
    # No history: bid based on health
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.85)
    return min(my_status['budget'], DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    num_alive = len(alive_opponents) + 1  # include self
    supply = day_context['supply']
    day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    
    # Collect yesterday's bids from opponents' previous_trace
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid: proportional to supply shortage or surplus
    # Total water needed by all alive players
    total_need = num_alive * WATER_REQ
    if supply >= total_need:
        base_bid = DAILY_SALARY * 0.35  # low pressure
    else:
        # competitive: bid higher if shortage is severe
        shortage = total_need - supply
        base_bid = DAILY_SALARY * (0.5 + 0.3 * (shortage / total_need))
    
    # Adjust based on yesterday's aggression
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        # If opponents were extremely aggressive, match but don't overbid
        if max_prev > DAILY_SALARY * 0.85:
            target_bid = max(base_bid, avg_prev * 0.9)
        else:
            target_bid = max(base_bid, avg_prev * 1.05)
    else:
        target_bid = base_bid
    
    # Survival consideration: if HP low, bid higher
    if my_hp <= 2:
        target_bid = max(target_bid, DAILY_SALARY * 0.85)
    elif my_hp <= 4:
        target_bid = max(target_bid, DAILY_SALARY * 0.65)
    
    # Cap by remaining budget and daily salary (cannot exceed salary)
    max_bid = min(my_budget, DAILY_SALARY)
    final_bid = min(target_bid, max_bid)
    # Ensure minimum 0.5 to avoid dead bid
    final_bid = max(final_bid, 0.5)
    
    return final_bid
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
    no_water_days = my_status['no_water_days']

    # Determine urgency based on hp and no_water_days
    needs_water = hp <= 2 or no_water_days >= 2

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            trace = opp.get('previous_trace', {})
            if trace and trace.get('bid') is not None:
                yesterday_bids.append(trace['bid'])

    # Compute base bid
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # If we need water, bid just above the highest yesterday bid
        if needs_water:
            bid = min(budget, max_yesterday + 2.0)
        else:
            # If hp is high, we can be conservative: 40% of salary or just above average
            avg_yesterday = sum(yesterday_bids) / len(yesterday_bids)
            bid = min(budget, max(DAILY_SALARY * 0.4, avg_yesterday - 5.0))
    else:
        # No opponent data, fallback based on need
        if needs_water:
            bid = min(budget, DAILY_SALARY * 0.9)
        else:
            bid = min(budget, DAILY_SALARY * 0.5)

    # Ensure bid is non-negative and respects supply constraints (can't bid more than budget? budget is after salary? but ok)
    bid = max(0.0, min(budget, bid))

    # Edge: if supply is very low, increase bid so we don't dehydrate
    if supply < 18 and needs_water:
        bid = min(budget, DAILY_SALARY * 0.95)
    elif supply < 18:
        bid = min(budget, DAILY_SALARY * 0.6)

    # Ensure we don't overbid if budget is low
    bid = min(budget, bid)
    return int(bid) if bid > 0 else 0.0
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        if highest_prev >= DAILY_SALARY * 0.85:
            if my_hp > 3:
                return min(my_budget, DAILY_SALARY * 0.3)
            return min(my_budget, DAILY_SALARY * 0.95)
        else:
            base = max(DAILY_SALARY * 0.5, highest_prev + 1.5)
            return min(my_budget, base)
    if my_hp <= 2:
        return min(my_budget, DAILY_SALARY * 0.9)
    return min(my_budget, DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(float(prev['bid']))

    # Default target if no traces
    if not yesterday_bids:
        target = DAILY_SALARY * 0.6
    else:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        # If we are desperate, slightly above average
        if hp <= 2 or no_water_days > 0:
            target = avg_prev * 1.05
        else:
            target = avg_prev * 0.95

    # Clamp to reasonable range
    min_bid = DAILY_SALARY * 0.4 if hp > 3 else DAILY_SALARY * 0.8
    max_bid = min(budget, DAILY_SALARY * 1.2)  # can't exceed budget
    final_bid = min(max_bid, max(min_bid, target))

    return int(final_bid) if final_bid > 0 else 0
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    supply = int(day_context['supply'])
    num_winners = supply // WATER_REQ
    
    alive = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    max_prev = max(yesterday_bids) if yesterday_bids else 0
    
    base = min(my_status['budget'], DAILY_SALARY
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])  # ensure int
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    n_alive = len(alive_opponents)

    # Estimate opponent bids from yesterday's trace
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))

    # Base bid strategy
    if hp <= 2:
        # Desperate: bid high to survive
        target_bid = min(budget, DAILY_SALARY * 1.1)
    elif hp <= 4:
        # Moderate health: need water soon
        target_bid = min(budget, DAILY_SALARY * 0.9)
    else:
        # Healthy: conservative
        target_bid = min(budget, DAILY_SALARY * 0.6)

    # Adjust for supply scarcity
    if supply < 20:
        target_bid *= 1.2
    elif supply < 18:
        target_bid *= 1.4

    # Snipe against known high bidders if we have budget and need
    if prev_bids and n_alive > 1:
        # Cindy tends to bid very high; avoid competition unless necessary
        max_prev = max(prev_bids)
        min_prev = min(prev_bids)
        # If we are healthy and supply is decent, bid just above the lower bids
        if hp > 3 and supply >= 20:
            target_bid = min(budget, max(target_bid, min_prev + 1.5))
        else:
            # Need to beat at least one opponent
            target_bid = min(budget, max(target_bid, max_prev + 1.5))

    # Ensure bid not negative and not exceed budget
    bid = max(0.0, min(budget, target_bid))
    # Round to 2 decimals to avoid floating point issues
    return round(bid, 2)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    water_units = int(supply // WATER_REQ)  # convert to int
    budget = my_status['budget']
    hp = my_status['hp']
    no_water = my_status['no_water_days']

    alive = [o for o in opponents_status.values() if o['alive']]
    if not alive:
        return min(budget, DAILY_SALARY * 0.4)

    # collect previous bids from alive opponents
    prev_bids = []
    for opp in alive:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    if not prev_bids:
        # no info: default conservative
        if hp <= 2:
            target = DAILY_SALARY * 0.8
        else:
            target = DAILY_SALARY * 0.5
        return min(budget, target)

    max_prev = max(prev_bids)

    # Determine aggression level
    desperate = (hp <= 2) or (no_water >= 1)
    moderate = (3 <= hp <= 5)
    healthy = (hp > 5)

    if desperate:
        # bid enough to beat the highest previous, but cap at budget and high fraction of salary
        target = max(DAILY_SALARY * 0.8, max_prev + 1)
    elif moderate:
        # bid to beat the highest if it's not too high, otherwise be cautious
        if max_prev < DAILY_SALARY * 0.6:
            target = max(DAILY_SALARY * 0.5, max_prev + 1)
        else:
            # previous high is already high, consider saving
            target = DAILY_SALARY * 0.4
    else: # healthy
        # can afford to skip a round if everyone bids high
        if max_prev > DAILY_SALARY * 0.7:
            target = DAILY_SALARY * 0.3
        else:
            target = max(DAILY_SALARY * 0.35, max_prev + 1)

    return min(budget, target)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Collect yesterday's bids from alive opponents
    yday_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            yday_bids.append(trace['bid'])
    
    hp = my_status['hp']
    budget = my_status['budget']
    day = day_context['day']
    supply = int(day_context['supply'])  # ensure integer for safety
    
    # Base bid: 0.5*salary if no info
    bid = DAILY_SALARY * 0.5
    
    if yday_bids:
        max_yday = max(yday_bids)
        if max_yday >= DAILY_SALARY * 0.85:
            # Opponents were aggressive yesterday; if we have health, undercut
            if hp > 3:
                bid = DAILY_SALARY * 0.3
            else:
                bid = DAILY_SALARY * 0.95
        else:
            # Low pressure: outbid yesterday's max slightly
            bid = max(DAILY_SALARY * 0.4, max_yday + 1.5)
    else:
        # No trace: default based on health
        if hp <= 2:
            bid = DAILY_SALARY * 0.9
        elif hp > 5:
            bid = DAILY_SALARY * 0.4
        else:
            bid = DAILY_SALARY * 0.6
    
    # Last day: go all in if healthy? Better save? Spend to survive.
    if day == 10:
        if hp <= 2:
            bid = min(budget, DAILY_SALARY * 1.0)
        else:
            bid = min(bid, budget * 0.8)
    
    # Ensure we don't exceed budget
    bid = min(bid, budget)
    # Ensure non-negative
    bid = max(0, bid)
    return float(bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    if not alive_opps:
        return min(budget, 1.0)
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace')
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])
    SALARY = 140
    MIN_SUPPLY = 15.0
    MAX_SUPPLY = 25.0
    if hp <= 2:
        target = min(budget, SALARY * 1.2)
        if yesterday_bids:
            max_yesterday = max(yesterday_bids)
            bid = max(target, max_yesterday + 0.01)
        else:
            bid = target
        return min(bid, budget)
    else:
        base = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY) * SALARY * 0.6
        if yesterday_bids:
            max_yesterday = max(yesterday_bids)
            desired = max(base, max_yesterday + 0.1)
            desired = min(desired, SALARY * 0.8)
        else:
            desired = base
        return min(desired, budget)
"""
