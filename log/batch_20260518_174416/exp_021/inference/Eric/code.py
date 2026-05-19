# ============================================================
# Experiment: exp_021
# Agent: Eric
# Source: exp_021
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    WATER_REQ = 8
    DAILY_SALARY = 140

    if hp <= 2:
        bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        bid = DAILY_SALARY * 0.7
    else:
        bid = DAILY_SALARY * 0.4

    if supply < 18:
        bid *= 1.2
    elif supply > 22:
        bid *= 0.8

    bid = min(bid, budget)
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    # Determine base bid as fraction of salary
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    # When supply is low (ratio near 0), bid higher; when high, bid lower
    base_bid = DAILY_SALARY * (0.7 - 0.3 * supply_ratio)

    # Adjust for HP and no_water_days
    if hp <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.85)
    if no_water > 0:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    # Use previous_trace to see if any opponent bid extremely high yesterday
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    max_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            max_prev_bid = max(max_prev_bid, prev['bid'])

    # If yesterday had a very high bid, we need to compete
    if max_prev_bid > DAILY_SALARY * 0.85:
        # Bid just above the average of high opponents to win
        avg_high = sum(o.get('previous_trace', {}).get('bid', 0) for o in alive_opponents if o.get('previous_trace', {}).get('bid', 0) > DAILY_SALARY * 0.5) / max(1, len([o for o in alive_opponents if o.get('previous_trace', {}).get('bid', 0) > DAILY_SALARY * 0.5]))
        base_bid = max(base_bid, avg_high + 2)

    # Ensure bid is within budget and positive integer
    bid = max(1, min(int(base_bid), int(budget)))
    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    last_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            last_bids.append(prev['bid'])

    # Determine baseline from opponents' previous bids
    if last_bids:
        avg_last_bid = sum(last_bids) / len(last_bids)
        # Expected opponent bid: slightly above average to account for increases
        expected_opponent_bid = avg_last_bid * 1.1
    else:
        expected_opponent_bid = DAILY_SALARY * 0.4

    # Own urgency and supply
    supply = day_context['supply']
    hp = my_status['hp']
    no_water = my_status['no_water_days']

    # Compute a baseline bid based on own needs
    # Lower supply means more competition -> raise bid
    supply_factor = 1 + (25 - supply) / 25
    hp_factor = 1 - min(hp / 10, 0.9)
    urgency = no_water * 10

    # Base bid: enough to get half of supply if multiple need, but capped
    base_bid = max(
        WATER_REQ * supply_factor * 5,
        DAILY_SALARY * 0.2
    )
    # Adjust for HP: lower HP -> need water more urgently
    if hp <= 3:
        base_bid = max(base_bid, DAILY_SALARY * 0.7)
    if no_water > 1:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    # Final bid: max of base and expected competitor
    bid = max(base_bid, expected_opponent_bid + 1)
    # Cap by budget
    bid = min(bid, my_status['budget'])
    # Never exceed salary
    bid = min(bid, DAILY_SALARY * 0.95)
    return bid
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

    alive_opponents = {aid: opp for aid, opp in opponents_status.items() if opp['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Gather yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    # Determine urgency based on health and no_water_days
    urgent = (hp <= 3) or (no_water_days >= 1)
    very_urgent = (hp <= 1) or (no_water_days >= 2)

    if very_urgent:
        # Need water desperately, bid high
        target = DAILY_SALARY * 0.95
    elif urgent:
        # Need water soon, bid moderately high
        target = DAILY_SALARY * 0.7
    else:
        # Not urgent, try to save
        target = DAILY_SALARY * 0.3

    # Adjust based on previous opponent bids
    if prev_bids:
        max_prev = max(prev_bids)
        # If opponents were very aggressive, don't compete unless urgent
        if max_prev >= DAILY_SALARY * 0.85:
            if not urgent:
                target = min(target, DAILY_SALARY * 0.2)
            else:
                # Still may need to outbid slightly
                target = max(target, max_prev + 1.0)
        else:
            # Opponents were moderate, adjust target to be competitive
            if urgent or very_urgent:
                target = max(target, max_prev + 1.0)
            else:
                target = min(target, max_prev * 0.8)

    # Ensure bid is within budget and not negative
    bid = int(min(budget, max(0.0, target)))
    return bid
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday's bids from previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Compute number of water units our requirement can cover
    max_units = int(supply // WATER_REQ)  # supply is float, convert to int

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        # If someone bid very high yesterday, they might be desperate
        if max_yesterday_bid >= DAILY_SALARY * 0.85:
            # If we are healthy, lowball; if low on HP, bid high
            if hp > 3:
                return min(budget, DAILY_SALARY * 0.3)
            else:
                return min(budget, DAILY_SALARY * 0.95)
        else:
            # Otherwise, try to stay competitive but not exceed budget
            target_bid = max(DAILY_SALARY * 0.5, max_yesterday_bid + 1.0)
            return min(budget, target_bid)

    # No previous traces (first day or new opponents)
    if hp <= 2:
        return min(budget, DAILY_SALARY * 0.9)
    # Default: moderate bid based on supply availability
    if max_units >= 1:
        # There is at least one water unit for each alive player? estimate
        # bid around 0.6 of salary to be safe
        return min(budget, DAILY_SALARY * 0.6)
    else:
        # Supply scarce, bid high to secure water
        return min(budget, DAILY_SALARY * 0.85)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    alive = {k: v for k, v in opponents_status.items() if v['alive']}
    prev_bids = [v['previous_trace']['bid'] for v in alive.values() if v.get('previous_trace') and v['previous_trace'].get('bid') is not None]
    max_prev = max(prev_bids) if prev_bids else None
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    if no_water > 0 or hp <= 2:
        if max_prev is None:
            return min(budget, DAILY_SALARY * 0.9)
        return min(budget, max(max_prev + 1.5, DAILY_SALARY * 0.85))
    elif hp >= 7:
        if max_prev is None:
            return min(budget, DAILY_SALARY * 0.45)
        return min(budget, max(DAILY_SALARY * 0.4, max_prev * 0.95))
    else:
        if max_prev is None:
            return min(budget, DAILY_SALARY * 0.6)
        return min(budget, min(DAILY_SALARY * 0.75, max_prev + 0.5))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
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

    # Calculate expected supply per player
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    num_opponents = len(alive_opponents)
    total_players = num_opponents + 1
    expected_share = supply / total_players

    # Determine base bid from opponents' previous bids
    max_prev_bid = 0.0
    for oid, opp in alive_opponents.items():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            if prev['bid'] > max_prev_bid:
                max_prev_bid = prev['bid']

    # Adjust bid based on urgency
    if hp <= 2 or no_water_days >= 2:
        # Desperate: bid high to ensure water
        target_bid = min(budget, DAILY_SALARY * 0.95)
    elif hp <= 4:
        # Moderately desperate: bid above max previous bid
        target_bid = max(max_prev_bid * 1.05, DAILY_SALARY * 0.6)
        target_bid = min(target_bid, budget, DAILY_SALARY * 0.9)
    else:
        # Comfortable: bid slightly above average previous to save money
        avg_prev_bid = 0.0
        count = 0
        for oid, opp in alive_opponents.items():
            prev = opp.get('previous_trace', {})
            if prev and 'bid' in prev and prev['bid'] is not None:
                avg_prev_bid += prev['bid']
                count += 1
        if count > 0:
            avg_prev_bid /= count
        else:
            avg_prev_bid = DAILY_SALARY * 0.5
        target_bid = max(avg_prev_bid * 1.02, DAILY_SALARY * 0.4)
        target_bid = min(target_bid, budget, DAILY_SALARY * 0.75)

    # Ensure we don't bid more than budget
    final_bid = min(target_bid, budget)
    # Ensure minimum bid if necessary to stay alive (but budget allows)
    final_bid = max(final_bid, 0)
    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Identify high-bid opponent (likely Cindy) from yesterday's trace
    high_bid_opp = None
    high_bid_amount = 0
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and 'bid' in prev and prev['bid'] is not None:
                bid = float(prev['bid'])
                if bid > high_bid_amount:
                    high_bid_amount = bid
                    high_bid_opp = opp_id
    
    # Base desire: how much we need water
    if hp <= 2 or no_water_days >= 2:
        need_urgency = 2
    elif hp <= 4:
        need_urgency = 1
    else:
        need_urgency = 0
    
    # Determine max safe bid (20% buffer for future)
    max_bid = min(budget, DAILY_SALARY * 0.95)
    
    # If there is a high-bid opponent, adjust
    if high_bid_opp and high_bid_amount > 0:
        # Assume they will bid at least 90% of yesterday's high bid if still alive
        expected_high = high_bid_amount * 0.9
        if need_urgency >= 2:
            # We must win: bid slightly above expected high
            target = expected_high + 2
        elif need_urgency == 1:
            # Bid moderately, but don't overpay
            target = min(expected_high * 0.85, DAILY_SALARY * 0.7)
        else:
            # We are safe, bid low to save money
            target = max(DAILY_SALARY * 0.2, expected_high * 0.3)
    else:
        # No known high bidder: go safe
        if need_urgency >= 2:
            target = DAILY_SALARY * 0.6
        elif need_urgency == 1:
            target = DAILY_SALARY * 0.4
        else:
            target = DAILY_SALARY * 0.2
    
    # Clamp to budget and 0.01
    bid = max(0.01, min(max_bid, target))
    return float(bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    
    supply = day_context['supply']
    day = int(day_context['day'])  # ensure int
    my_hp = int(my_status['hp'])
    my_budget = my_status['budget']
    
    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}
    
    # Determine yesterday's highest bid among alive opponents
    max_prev_bid = 0
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = prev['bid']
            if bid > max_prev_bid:
                max_prev_bid = bid
    
    # Base bid: half salary
    base_bid = DAILY_SALARY * 0.5  # 70
    
    # Adjust based on supply scarcity
    if supply <= MIN_SUPPLY + 2:  # supply <= 17
        supply_factor = 1.3
    elif supply <= (MIN_SUPPLY + MAX_SUPPLY) / 2:  # <= 20
        supply_factor = 1.15
    else:
        supply_factor = 1.0
    
    # Adjust based on HP
    if my_hp <= 2:
        hp_factor = 1.5
    elif my_hp <= 4:
        hp_factor = 1.2
    else:
        hp_factor = 1.0
    
    # Consider yesterday's max bid: if someone bid very high (>salary), they might still be rich; but they could also be saving today. I'll add a small increment only if my HP is critical.
    threat_increment = 0
    if max_prev_bid > DAILY_SALARY * 0.85 and my_hp <= 3:
        threat_increment = 5
    
    bid = base_bid * supply_factor * hp_factor + threat_increment
    
    # Cap: do not exceed budget or 1.3 * salary
    max_bid = min(my_budget, DAILY_SALARY * 1.3)
    bid = min(bid, max_bid)
    
    # Ensure minimum bid if HP is extremely low
    if my_hp <= 1:
        bid = max(bid, DAILY_SALARY * 0.9)
    
    # Final bounding
    bid = max(1, min(bid, my_budget))
    return int(bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Extract yesterday's bids from previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    highest_prev = max(yesterday_bids) if yesterday_bids else 0
    
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    supply = day_context['supply']
    
    # Base bid calculation
    if hp <= 2 or no_water > 0:
        # desperate: bid high to secure water
        desired_bid = DAILY_SALARY * 0.9
    elif hp > 5:
        # comfortable: save budget
        desired_bid = DAILY_SALARY * 0.3
    else:
        # moderate: try to beat yesterday's highest bid by a small margin, but not too much
        if highest_prev > 0:
            desired_bid = max(DAILY_SALARY * 0.5, highest_prev + 1.0)
        else:
            desired_bid = DAILY_SALARY * 0.55
    
    # Adjust for supply: if supply is low, increase bid to be more competitive
    if supply < 18:
        desired_bid *= 1.2
    
    # Ensure we never bid more than budget (and at least 0)
    bid = min(budget, max(0, desired_bid))
    return bid
"""
