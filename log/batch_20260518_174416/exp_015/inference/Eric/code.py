# ============================================================
# Experiment: exp_015
# Agent: Eric
# Source: exp_015
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.3)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Assess median pressure
    if yesterday_bids:
        sorted_bids = sorted(yesterday_bids)
        n = len(sorted_bids)
        median_bid = sorted_bids[int(n // 2)]  # float index protected
        max_prev = max(sorted_bids)
    else:
        median_bid = 0
        max_prev = 0

    # Determine base bid
    if hp <= 2:
        # Desperate: must get water
        base = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 4:
        # Moderate need
        if max_prev >= DAILY_SALARY * 0.8:
            base = min(budget, DAILY_SALARY * 0.45)
        else:
            base = min(budget, median_bid + 0.5 * DAILY_SALARY)
    else:
        # Healthy: conserve budget
        base = min(budget, DAILY_SALARY * 0.35)

    # Ensure we don't bid more than budget
    bid = min(base, budget)

    # Small random variation for unpredictability (if budget permits)
    import random
    variation = random.uniform(-2, 2)
    bid = max(0, bid + variation)

    return round(bid, 2)
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # gather yesterday's bids from traces
    yesterday_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            yesterday_bids.append(float(trace['bid']))

    # base bid depends on urgency
    if hp <= 3 or no_water_days >= 1:
        # critical: need water now
        base = DAILY_SALARY * 0.9
    elif hp <= 6:
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * 0.35

    # adjust based on yesterday's highest bid
    if yesterday_bids:
        highest_yesterday = max(yesterday_bids)
        # if opponents were aggressive, increase bid
        if highest_yesterday > DAILY_SALARY * 0.7:
            base = max(base, DAILY_SALARY * 0.75)
        # if we can afford to outbid them by a small margin, do so
        if budget >= highest_yesterday + 0.1:
            base = max(base, highest_yesterday + 0.1)

    # also consider supply: if low supply, competition higher
    if supply < 18 and len(alive_opponents) >= 2:
        base *= 1.2

    # never bid more than budget
    bid = min(budget, base)
    # ensure min positive if we have budget
    if budget > 0:
        bid = max(bid, 0.1)
    else:
        bid = 0.0
    return round(bid, 2)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    max_winners = supply // WATER_REQ
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_max_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_max_bid = max(yesterday_max_bid, prev['bid'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    if hp <= 2 or no_water_days >= 1:
        target = max(DAILY_SALARY * 0.9, yesterday_max_bid + 1.5)
        return min(budget, target)
    else:
        if len(alive_opponents) < max_winners:
            return min(budget, max(10, DAILY_SALARY * 0.4))
        else:
            return min(budget, max(10, DAILY_SALARY * 0.5))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    # Calculate how much water we need (max we can get is supply)
    # Estimate number of water units available per player (supply / WATER_REQ)
    units_available = int(supply // WATER_REQ)  # total units of water
    
    # Sort opponents by their previous bid (if available) to gauge pressure
    opponent_list = []
    for oid, o in opponents_status.items():
        if o['alive']:
            prev = o.get('previous_trace', {})
            prev_bid = prev.get('bid', None)
            if prev_bid is not None:
                opponent_list.append((oid, float(prev_bid)))
    
    # If no opponent history, assume moderate
    if not opponent_list:
        # Default bid based on HP
        if hp <= 2:
            return min(budget, DAILY_SALARY * 0.9)
        else:
            return min(budget, DAILY_SALARY * 0.4)
    
    # Sort by previous bid descending
    opponent_list.sort(key=lambda x: x[1], reverse=True)
    highest_prev = opponent_list[0][1]
    second_highest_prev = opponent_list[1][1] if len(opponent_list) > 1 else 0
    
    # Determine how many water units we need (we need at least 1 unit to survive, but 8 water = 1 unit)
    # Actually each unit is 1 water, but water_requirement is 8, so we need 8 units per day? No: water_requirement is amount of water needed per day. The supply is total water available that day. So each unit is 1 water. So we need 8 units. But supply is total. So we must win enough water to cover our need.
    # Since bidding is per unit? Actually bid is per unit? The game description: bid amount for water? Typically you bid for a portion of supply. But the average bids from previous meta-round (Alex 109, Cindy 132) suggest they bid high amounts, likely total bid. So we need to consider that.
    # For simplicity, we assume each agent bids a single amount and the highest bidder gets as much water as they need (up to supply) and pays their bid. So we need to outbid others to get 8 units.
    
    # Strategy: if we are desperate, bid slightly above second-highest previous bid (if affordable)
    # Otherwise, bid low to save money.
    
    # Determine if we need to win today
    days_left = 10 - day  # total episode days is 10
    # Not exactly, but we can use day to estimate remaining
    
    # If HP is critical (<=2), we must win
    if hp <= 2:
        target_bid = highest_prev + 1.0
        if target_bid > budget:
            return budget  # go all in
        return min(budget, target_bid)
    
    # If we have high HP, we can afford to lose occasionally
    if hp > 5:
        # Bid low to save, but not zero (so we might win if others low)
        return min(budget, DAILY_SALARY * 0.3)
    
    # Moderate HP: try to win but not overpay
    # Estimate how many other bidders have high previous bids
    high_bidders = [b for _, b in opponent_list if b > DAILY_SALARY * 0.7]
    if len(high_bidders) >= 2:
        # Strong competition, avoid bidding war unless necessary
        # Bid just below moderate to stay safe
        return min(budget, second_highest_prev * 0.95)
    else:
        # One strong bidder or none: bid just above the second highest if we can afford
        bid = second_highest_prev + 1.0
        if bid > budget:
            bid = budget
        return min(budget, bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    budget = my_status['budget']
    hp = my_status['hp']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine urgency
    urgent = False
    if hp <= 2 or no_water_days >= 1:
        urgent = True
    
    # Base conservative bid
    base_bid = min(budget, DAILY_SALARY * 0.55)
    
    # If urgent, bid higher
    if urgent:
        base_bid = min(budget, DAILY_SALARY * 0.95)
    
    # Consider yesterday's max bid
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # If someone bid very high, either outbid them (if urgent) or stay moderate
        if max_yesterday > DAILY_SALARY * 0.85:
            if urgent:
                base_bid = max(base_bid, min(budget, max_yesterday + 1.0))
            else:
                base_bid = min(base_bid, DAILY_SALARY * 0.4)
        else:
            # Slightly above yesterday's max if we need water, otherwise stay
            if urgent:
                base_bid = max(base_bid, min(budget, max_yesterday + 2.0))
            else:
                base_bid = max(base_bid, min(budget, max_yesterday + 1.0) if max_yesterday < DAILY_SALARY * 0.5 else min(budget, max_yesterday * 0.9))
    
    # Ensure we don't bid more than necessary given supply
    supply = day_context['supply']
    # If supply is low, competition high, consider increasing
    if supply < 18 and not urgent:
        base_bid = min(budget, base_bid * 1.2)
    
    # Final cap at budget
    return min(budget, base_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = day_context['supply']
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive = [o for o in opponents_status.values() if o['alive']]
    
    # Base bid calculation
    if hp <= 2 or no_water_days >= 2:
        base_bid = min(budget, 140 * 0.95)
    else:
        # Look at yesterday's highest bid among alive opponents
        high_prev = 0
        for opp in alive:
            prev = opp.get('previous_trace', {})
            if prev and 'bid' in prev:
                bid = prev['bid']
                if bid is not None and bid > high_prev:
                    high_prev = bid
        if high_prev > 120:
            base_bid = min(budget, 140 * 0.75)
        elif high_prev > 80:
            base_bid = min(budget, 140 * 0.55)
        else:
            base_bid = min(budget, 140 * 0.35)
    
    # Adjust for supply scarcity
    if supply < 20:
        bid = min(budget, base_bid * 1.2)
    else:
        bid = base_bid
    
    # Ensure at least a small bid to avoid bid = 0? But we can bid 0 if needed?
    # To be safe, keep a non-negative bid, but if budget is 0 then 0
    bid = max(0.0, min(bid, budget))
    return float(bid)
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine base bid from yesterday's activity
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
    else:
        highest_prev = 0
        avg_prev = 0
    
    # Supply factor: lower supply means higher competition
    supply_factor = 1.0 + (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)  # 1.0 to 2.0
    
    # Need factor: desperate if hp low or no water
    need_factor = 1.0
    if hp <= 3 or no_water_days > 0:
        need_factor = 1.5
    if hp <= 1 or no_water_days >= 2:
        need_factor = 2.0
    
    # Compute target bid
    if highest_prev > DAILY_SALARY * 1.5:
        # Very aggressive opponent yesterday, be cautious if we are healthy
        if hp > 5:
            target = max(DAILY_SALARY * 0.6, avg_prev * 0.8)
        else:
            target = max(DAILY_SALARY * 0.9, highest_prev * 0.95)
    else:
        # Normal competition
        target = max(DAILY_SALARY * 0.5, avg_prev + 1.0)
    
    # Apply factors
    bid = target * supply_factor * need_factor
    bid = min(bid, budget)  # cannot exceed budget
    bid = max(bid, 1.0)     # minimum bid at least 1
    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    supply = int(day_context['supply'])
    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    alive_opponents = {oid: opp for oid, opp in opponents_status.items() if opp['alive']}
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))
    # Base bid computation
    if my_hp <= 2:
        # desperate: bid high
        bid = min(my_budget, DAILY_SALARY * 0.9)
    elif supply >= 20:
        # abundant water, conserve
        bid = min(my_budget, DAILY_SALARY * 0.4)
    else:
        # competitive: try to outbid highest yesterday if necessary
        if yesterday_bids:
            max_yesterday = max(yesterday_bids)
            # If opponent were very high (near salary), they might decrease today, so stay low
            if max_yesterday >= DAILY_SALARY * 0.85:
                if my_hp > 3:
                    bid = min(my_budget, DAILY_SALARY * 0.3)
                else:
                    bid = min(my_budget, DAILY_SALARY * 0.95)
            else:
                # slightly above the highest yesterday, but not too high
                bid = min(my_budget, max(DAILY_SALARY * 0.5, max_yesterday + 1.5))
        else:
            # no yesterday data, use moderate default
            bid = min(my_budget, DAILY_SALARY * 0.55)
    # Ensure bid is not negative
    return max(0.0, bid)
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
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    # Estimate possible winners
    num_winners = int(supply // WATER_REQ)
    # Collect previous bids from opponents
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    # Base bid: proportional to supply scarcity
    scarcity_factor = 1.0 - (supply / 25)
    base_bid = DAILY_SALARY * (0.6 + 0.3 * scarcity_factor)
    # Aggression based on own health
    if hp <= 2 or no_water_days >= 1:
        aggression = 1.1
    elif hp <= 4:
        aggression = 0.9
    else:
        aggression = 0.7
    # Adjust based on opponents' last bids
    if prev_bids:
        max_prev = max(prev_bids)
        # If supply is small and opponents bid high, we may need to outbid
        if num_winners <= 1:
            if max_prev > base_bid * 0.8:
                target = max_prev + 1.5
            else:
                target = max_prev + 2.5
        else:
            # More winners, less pressure
            target = max(base_bid * aggression, max_prev * 0.95)
    else:
        target = base_bid * aggression
    # Ensure we don't exceed budget or bid zero unnecessarily
    target = max(target, 5.0)
    target = min(target, budget)
    # Conservative end-game if budget low
    if budget < DAILY_SALARY * 2 and hp > 5:
        target = min(target, DAILY_SALARY * 0.4)
    return target
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    # Base bid: if hp low or no water days > 0, bid higher
    if hp <= 2 or no_water_days >= 1:
        base_bid = DAILY_SALARY * 0.9
    else:
        base_bid = DAILY_SALARY * 0.4
    # Adjust based on yesterday's opponent max bid if available
    yesterday_max = 0
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            yesterday_max = max(yesterday_max, trace['bid'])
    if yesterday_max > 0:
        # If opponents bid high yesterday, they likely continue; to avoid overpaying, reduce my bid slightly
        if yesterday_max >= DAILY_SALARY * 0.85:
            adjusted = base_bid * 0.6
        else:
            adjusted = max(base_bid, yesterday_max + 2.0)
    else:
        adjusted = base_bid
    # Ensure we don't exceed budget and stay within supply * WATER_REQ? Actually supply is max units, each unit costs bid
    # But we bid per unit? Actually competition: we bid a price, and the highest bids get water up to supply. So we can bid up to budget.
    # To be safe, cap at budget
    bid = min(budget, adjusted)
    # Also ensure non-negative
    bid = max(0, bid)
    return float(bid)
"""
