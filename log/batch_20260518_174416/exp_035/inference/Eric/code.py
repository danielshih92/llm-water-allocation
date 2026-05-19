# ============================================================
# Experiment: exp_035
# Agent: Eric
# Source: exp_035
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, SALARY * 0.5)
    urgent = (hp <= 2) or (no_water_days > 1)
    avg_opp_hp = sum(o['hp'] for o in alive_opponents) / len(alive_opponents)
    base_bid = SALARY * (1 - hp / 10.0) * 0.8
    if avg_opp_hp > 6:
        base_bid *= 0.6
    else:
        base_bid *= 1.2
    bid = min(budget, max(base_bid, SALARY * 0.3))
    if urgent:
        bid = max(bid, SALARY * 0.9)
    else:
        bid = min(bid, SALARY * 0.6)
    bid = max(0.0, min(budget, bid))
    return bid
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
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Extract yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine base bid strategy
    if my_status['hp'] <= 3:
        # Desperate: need water
        target_bid = min(my_status['budget'], DAILY_SALARY * 0.9)
    else:
        # Healthy: can be conservative
        if yesterday_bids:
            max_prev = max(yesterday_bids)
            # If we are in danger (low hp) use 0.9, else use 0.4
            if my_status['hp'] <= 5:
                target_bid = min(my_status['budget'], max(DAILY_SALARY * 0.5, max_prev + 1.0))
            else:
                target_bid = min(my_status['budget'], DAILY_SALARY * 0.4)
        else:
            target_bid = min(my_status['budget'], DAILY_SALARY * 0.5)
    
    # Ensure we don't overpay beyond necessity (water cost = supply? But we don't know winner's price)
    # Conservative: keep within budget and salary
    bid = max(0.0, min(my_status['budget'], target_bid))
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
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Estimate number of alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_opp = len(alive_opponents)

    # Estimate opponent average water requirement from previous trace if available
    # Use default assumption of 8 if no data
    opp_water_req = 8
    if previous_trace_available(alive_opponents):
        water_requirements = []
        for opp in alive_opponents:
            prev = opp.get('previous_trace', {})
            if prev and 'bid' in prev:
                # Not water requirement, but we ignore
                pass
    
    # Base bid: fraction of salary depending on supply and hp
    # If supply is low, we need to bid higher to secure water
    # If hp is low, we must bid aggressively
    # If no_water_days > 0, immediate need

    # Determine water availability per person
    # Total potential water need: (num_opp + 1) * WATER_REQ (assuming all same req)
    # But we don't know opponent req. Use supply per person as indicator
    supply_per_agent = supply / (num_opp + 1) if (num_opp + 1) > 0 else supply

    # Base bid from salary
    if supply_per_agent >= WATER_REQ:
        # Plenty of water, we can bid low
        base_bid = DAILY_SALARY * 0.3
    else:
        # Scarcity, bid higher
        base_bid = DAILY_SALARY * 0.6

    # Adjust for hp
    if hp <= 3:
        # Critical, bid high
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    if no_water_days >= 2:
        base_bid = min(budget, DAILY_SALARY * 0.95)

    # Ensure we don't exceed budget
    bid = min(budget, base_bid)

    # On early days, try to conserve if possible
    if day <= 2 and hp > 5 and supply_per_agent >= WATER_REQ:
        bid = min(bid, DAILY_SALARY * 0.2)

    # Add slight random noise to avoid predictability? Not allowed, deterministic
    # Round to 2 decimals
    bid = round(bid, 2)
    return bid

# Helper function not needed in code, since we didn't use it
def previous_trace_available(opponents):
    for opp in opponents:
        if opp.get('previous_trace', {}).get('bid') is not None:
            return True
    return False
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Get yesterday's highest bid from alive opponents
    max_prev_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            if prev['bid'] > max_prev_bid:
                max_prev_bid = prev['bid']

    # Determine maximum possible winners based on supply
    max_winners = int(supply // WATER_REQ)
    low_competition = len(alive_opponents) <= max_winners

    # Urgency based on health
    urgent = hp <= 2

    # Decide bid amount
    if max_prev_bid > 0:
        if urgent:
            # Need water desperately, bid just above highest previous
            bid = min(budget, max_prev_bid + 1.5)
        else:
            # Not urgent, try to conserve by bidding lower if competition allows
            if low_competition:
                bid = min(budget, DAILY_SALARY * 0.4)
            else:
                # Still outbid if previous was very high
                if max_prev_bid >= DAILY_SALARY * 0.8:
                    bid = min(budget, DAILY_SALARY * 0.5)
                else:
                    bid = min(budget, max_prev_bid + 1.0)
    else:
        # No previous data, use simple heuristic based on supply and health
        if urgent:
            bid = min(budget, DAILY_SALARY * 0.9)
        elif low_competition:
            bid = min(budget, DAILY_SALARY * 0.3)
        else:
            bid = min(budget, DAILY_SALARY * 0.6)

    # Ensure non-negative and not exceeding budget
    bid = max(0.0, min(budget, bid))
    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Extract yesterday's bids from previous_trace of alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine urgency
    urgent = (hp <= 2 or no_water_days >= 2)

    # Base bid from urgency
    if urgent:
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
    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    
    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}
    num_alive = len(alive_opponents)
    
    # Estimate max opponent bid from previous traces
    max_opp_bid = 0.0
    for aid, opp in alive_opponents.items():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            opp_bid = float(prev['bid'])
            if opp_bid > max_opp_bid:
                max_opp_bid = opp_bid
    
    # Urgency factor: low hp = need water
    hp_threshold = 3
    if my_hp <= hp_threshold:
        base_bid = DAILY_SALARY * 0.9
    else:
        base_bid = DAILY_SALARY * 0.5
    
    # Adjust based on supply: if supply is high, competition may be less
    supply_ratio = supply / (num_alive + 1) / WATER_REQ
    if supply_ratio < 0.5:
        scarcity_penalty = 1.2
    else:
        scarcity_penalty = 1.0
    base_bid *= scarcity_penalty
    
    # If opponent max bid is significant, consider beating it to secure water
    if max_opp_bid > 0:
        # If we really need water, outbid by small margin
        if my_hp <= hp_threshold:
            target_bid = max_opp_bid + 1.0
        else:
            # Otherwise just follow market
            target_bid = base_bid
    else:
        target_bid = base_bid
    
    # Ensure bid within budget and not more than salary (to preserve capital)
    target_bid = min(target_bid, my_budget)
    target_bid = min(target_bid, DAILY_SALARY * 1.2)  # cap at 120% salary
    target_bid = max(target_bid, 0.0)
    
    return target_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])  # ensure integer
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Gather yesterday's bids from alive opponents
    prev_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            trace = opp.get('previous_trace', {})
            if trace and 'bid' in trace and trace['bid'] is not None:
                prev_bids.append(trace['bid'])

    # Determine baseline bid
    if not prev_bids:
        # No data: conservative start
        base_bid = DAILY_SALARY * 0.5
    else:
        max_prev = max(prev_bids)
        if max_prev > DAILY_SALARY * 0.8:
            # Opponents were aggressive yesterday – try to undercut a bit to save budget
            base_bid = max(DAILY_SALARY * 0.4, max_prev - 10)
        else:
            # Opponents were moderate – match the highest to secure water
            base_bid = max_prev + 2

    # Adjust for personal urgency
    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(base_bid, DAILY_SALARY * 0.85))
    else:
        bid = min(budget, base_bid)

    # Ensure not to exceed budget
    bid = max(0, min(bid, budget))
    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    # Aggressive: use full budget to secure water on day 1
    return my_status['budget']
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
    
    budget = my_status['budget']
    hp = my_status['hp']
    supply = int(day_context['supply'])  # ensure int
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    # Get highest previous bid from alive opponents
    highest_prev_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid_val = prev['bid']
            if bid_val > highest_prev_bid:
                highest_prev_bid = bid_val
    
    # Base bid: moderate level
    target_bid = DAILY_SALARY * 0.65  # 91
    
    # If previous competition was high, outbid by a margin
    if highest_prev_bid > 100:
        target_bid = max(target_bid, highest_prev_bid + 5)
    
    # If low hp, bid aggressively to secure water
    if hp <= 2:
        target_bid = max(target_bid, DAILY_SALARY * 1.1)  # 154
    
    # Ensure we don't exceed budget
    final_bid = min(budget, target_bid)
    # Also ensure non-negative and reasonable
    final_bid = max(0, final_bid)
    
    return final_bid
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
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))
    
    # Determine base bid
    # Supply scarcity factor: lower supply means higher need
    scarcity = 1.0 + max(0.0, (MAX_SUPPLY - supply) / MAX_SUPPLY) * 0.5  # 1.0 to 1.5
    base = min(budget, DAILY_SALARY * 0.6 * scarcity)
    
    # Adjust based on previous bids
    if prev_bids:
        max_prev = max(prev_bids)
        # If opponents were aggressive, match but don't exceed budget
        if max_prev > DAILY_SALARY * 0.8 and hp > 2:
            # Try to undercut by a small margin to save money
            target = max(base, max_prev * 0.9)
        elif hp <= 2 or no_water_days > 0:
            # Desperate: bid higher to secure water
            target = max(base, DAILY_SALARY * 0.8)
        else:
            # Normal: stay near base but slightly above average if needed
            avg_prev = sum(prev_bids) / len(prev_bids)
            target = max(base, avg_prev * 0.95)
    else:
        # First day: use base
        target = base
    
    # Final sanity: cannot bid more than budget, and must be positive
    return min(int(budget), max(1.0, target))
"""
