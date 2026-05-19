# ============================================================
# Experiment: exp_059
# Agent: Eric
# Source: exp_059
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, 1.0)
    # Base bid: need-based
    # If low HP, bid aggressively; else moderate
    if hp <= 2:
        bid = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 4:
        bid = min(budget, DAILY_SALARY * 0.6)
    else:
        bid = min(budget, DAILY_SALARY * 0.4)
    # Adjust based on previous day's opponent max bid if available
    max_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            max_prev_bid = max(max_prev_bid, prev['bid'])
    if max_prev_bid > 0:
        # If opponents bid high yesterday, we may need to match
        if hp <= 3:
            bid = max(bid, min(budget, max_prev_bid * 1.1))
        else:
            bid = max(bid, min(budget, max_prev_bid * 0.95))
    # Ensure bid is positive
    bid = max(bid, 0.01)
    # Cap at budget
    bid = min(bid, budget)
    # Use int on any index operations (none here)
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    if not alive_opps:
        return int(min(my_status['budget'], DAILY_SALARY * 0.45))

    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    if prev_bids:
        max_prev = max(prev_bids)
        if max_prev >= DAILY_SALARY * 1.0:
            base = DAILY_SALARY * 0.78
        elif max_prev >= DAILY_SALARY * 0.8:
            base = DAILY_SALARY * 0.65
        else:
            base = DAILY_SALARY * 0.50
    else:
        base = DAILY_SALARY * 0.45

    if my_status['hp'] <= 2:
        base = max(base, DAILY_SALARY * 0.85)
    elif my_status['hp'] <= 4:
        base = max(base, DAILY_SALARY * 0.65)

    bid = int(min(my_status['budget'], base))
    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    day = int(day_context['day'])
    supply = int(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']

    # Base bid by day phase
    if day <= 3:
        base = 40
    elif day <= 6:
        base = 80
    else:
        base = 120

    # HP adjustment
    if hp <= 2:
        base = min(base + 30, DAILY_SALARY)
    elif hp <= 5:
        base += 10

    # Opponent yesterday max bid exploitation
    max_yesterday = 0
    for opp in opponents_status.values():
        prev = opp.get('previous_trace')
        if prev and prev.get('bid') is not None:
            max_yesterday = max(max_yesterday, prev['bid'])

    if max_yesterday > 0:
        target = max(base, max_yesterday + 2)
        if target > DAILY_SALARY * 0.9:
            target = DAILY_SALARY * 0.9
        base = target

    bid = max(0.0, min(float(budget), float(base)))
    return bid
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

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

    highest_yesterday = max(yesterday_bids) if yesterday_bids else 0.0

    # Base bid: ensure water if needed
    supply = day_context['supply']
    day = day_context['day']

    # Determine urgency based on health and no_water_days
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # If health is critical (hp <= 1 or no_water_days >= 1), must win
    if hp <= 1 or no_water_days >= 1:
        # Bid enough to win: slightly above yesterday's highest or a safe fraction of budget
        bid = min(budget, max(DAILY_SALARY * 0.9, highest_yesterday + 2.0))
    else:
        # Otherwise, bid conservatively but enough to survive if many opponents
        num_alive = sum(1 for o in opponents_status.values() if o['alive'])
        # If we have many opponents, we may need to bid higher
        if num_alive >= 3:
            target = max(DAILY_SALARY * 0.6, highest_yesterday * 0.8)
        else:
            target = max(DAILY_SALARY * 0.4, highest_yesterday * 0.6)
        bid = min(budget, target)

    # Ensure bid is non-negative and not exceed budget
    bid = max(0.0, min(bid, budget))

    # If supply is very low, be more aggressive
    if supply <= MIN_SUPPLY + 2:
        bid = max(bid, min(budget, DAILY_SALARY * 0.85))

    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    num_winners = supply // WATER_REQ
    if num_winners == 0:
        return 0

    opponent_bids = []
    for opp_id, opp in opponents_status.items():
        if not opp['alive']:
            continue
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            opponent_bids.append(prev['bid'])
        else:
            # Default assumption if no trace: medium bid
            opponent_bids.append(DAILY_SALARY * 0.5)

    # Sort descending
    opponent_bids.sort(reverse=True)
    # Determine threshold: we need to beat the (num_winners-1)th opponent if we enter
    if len(opponent_bids) < num_winners:
        threshold = 0  # easy to win
    else:
        threshold = opponent_bids[num_winners - 1]

    # My urgency
    hp = my_status['hp']
    no_water = my_status['no_water_days']
    budget = my_status['budget']

    if no_water >= 2 or hp <= 2:
        # Desperate, bid high up to budget
        bid = min(budget, DAILY_SALARY * 0.95)
    elif no_water == 1 or hp <= 4:
        # Moderate need, beat threshold with small margin
        bid = min(budget, max(threshold + 1, DAILY_SALARY * 0.6))
    else:
        # Healthy, try to save money
        bid = min(budget, max(threshold + 0.5, DAILY_SALARY * 0.4))

    # Ensure bid is non-negative and not exceeding budget
    bid = max(0, min(bid, budget))
    # Also cap at a reasonable maximum to avoid overbidding
    if bid > DAILY_SALARY * 0.9 and hp > 5 and no_water == 0:
        bid = min(bid, DAILY_SALARY * 0.75)
    return bid
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_opponents = len(alive_opponents)

    # Base bid: fraction of daily salary, adjusted by supply scarcity
    # Supply relative to max
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    # When supply is low, we need higher bid
    if supply_ratio < 0.3:
        base_bid = DAILY_SALARY * 0.8
    elif supply_ratio < 0.6:
        base_bid = DAILY_SALARY * 0.65
    else:
        base_bid = DAILY_SALARY * 0.5

    # Look at yesterday's opponent bids from previous_trace
    opponent_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            opponent_bids.append(prev['bid'])

    if opponent_bids:
        highest_prev = max(opponent_bids)
        avg_prev = sum(opponent_bids) / len(opponent_bids)
        # Adjust base upward if opponents were aggressive
        if highest_prev > DAILY_SALARY * 0.8:
            base_bid = max(base_bid, avg_prev * 1.1)
        else:
            base_bid = max(base_bid, avg_prev * 1.05)

    # HP urgency
    if hp <= 2:
        multiplier = 1.0
    elif hp <= 5:
        multiplier = 0.85
    else:
        multiplier = 0.7

    # No water days increase urgency
    if no_water_days > 0:
        multiplier = min(1.0, multiplier + 0.1 * no_water_days)

    # Consider number of opponents: more opponents, higher competition
    opponent_factor = 1.0 + 0.05 * num_opponents

    bid = base_bid * multiplier * opponent_factor

    # Ensure we don't exceed budget
    bid = min(bid, budget)
    # Minimum positive bid to participate
    bid = max(bid, 1.0)

    # Round to avoid floating issues? Not required but safe
    bid = round(bid, 2)

    return int(bid) if bid >= 1 else 1.0
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    daily_salary = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            prev_bids.append(prev['bid'])
    if prev_bids:
        max_prev = max(prev_bids)
        if max_prev > daily_salary * 0.8:
            if hp > 3:
                bid = min(budget, daily_salary * 0.3)
            else:
                bid = min(budget, daily_salary * 0.9)
        else:
            bid = min(budget, max(daily_salary * 0.4, max_prev + 2))
    else:
        if hp <= 2:
            bid = min(budget, daily_salary * 0.85)
        else:
            bid = min(budget, daily_salary * 0.5)
    bid = max(0, bid)
    return min(budget, bid)
"""
